"""Report data for SBML models and COMBINE archives.

The report of a model is the `Report` created by `SBMLDocumentInfo`. A single
SBML file is wrapped in a COMBINE archive with one master model, so that the
frontend always receives an archive manifest with one report per SBML entry.

The reports of one archive are linked together: an external model definition of
comp is resolved against the other entries (`external.py`), and the link graph
of an entry follows it into the report of the entry it names (`links.py`).
Nothing is fetched. A single file which was read from a trusted directory, which
is one the operator or the user chose and never the temporary file of an upload,
gains the files next to it which its external model definitions name as further
entries of its archive.

An archive is extracted into a temporary directory of its own, which is removed
when the report is built. The content of a request is read within the limits of
`limits.py`: a gzipped model is decompressed up to `MAX_CONTENT_SIZE`, and an
archive is checked for the number, the size and the compression of its entries
before it is extracted.

The report of a source which is not trusted is built in a child process
(`report_gzip` run by `isolation.py`), which answers it as the gzipped JSON the
server sends, so that a document which ends the process of libsbml is an error
of one request and not an outage of the server. The ODE file of such a source
is written in a child of its own as well (`ode_source`), which reads the
content through sbmlsim-core and libsbml the same way. `report_for_path` and
`ode_for_path` build in the process which calls them, for a trusted path: the
examples and the file the user gave the local server of `show`.

The equations of an entry whose comp submodels expand beyond the budget of the
expanded size are not built (`_odes`): the shared Rust expansion holds every
instantiated element into one model, so a document of a few kilobytes can ask
for more memory than a child may use, and the report keeps its elements and
says in its `ode_error` why it has no equations.

The validation of libsbml is not part of the report: `validation_for_path`
reads the entries of a source the same way, without their link graph, and
checks them, all of it in a child process as well, so that the report is
answered as fast as it is built and its validation when it is finished.
"""

import gzip
import hashlib
import logging
import tempfile
import time
import uuid
import zipfile
from collections.abc import Generator, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import libsbml
from pymetadata.omex import EntryFormat, Omex
from pymetadata.omex import ManifestEntry as OmexManifestEntry

from sbml4humans import isolation, limits, native, validation
from sbml4humans.external import ExternalModels, normalize_location, resolve_source
from sbml4humans.limits import ContentTooLargeError, format_size
from sbml4humans.links import LinkSource, build_link_graphs
from sbml4humans.model import (
    Debug,
    EntryValidation,
    Manifest,
    ManifestEntry,
    ReportEntry,
    ReportResponse,
    ValidationResponse,
)
from sbml4humans.odes import analyse, ode_system
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.validation import (
    ReportDocuments,
    instantiated_elements,
    issues_of,
    validate,
)


logger = logging.getLogger(__name__)

# location of a single SBML file in the archive created for it
SBML_LOCATION = "./model.xml"
GZIP_MAGIC = b"\x1f\x8b"
# the bytes decompressed at a time
CHUNK_SIZE = 1024 * 1024  # [byte]
# the level the JSON of a report is gzipped at, by the child of a report and by
# the api. A moderate level: the reports compress about 20 fold already at this
# level, and a higher one costs time on every large report for a few percent
REPORT_GZIP_LEVEL = 5

# what a client reads where the equations of a model were not built because its
# comp submodels expand beyond the budget of the expanded size, the one failure
# of the ODE system which is none of sbmlsim-core
_NOT_FLATTENED = (
    "The equations of the model were not built: it expands by its comp "
    "submodels to {size:,} elements, more than the {budget:,} elements a model "
    "may expand to."
)


class _Entry:
    """The report of one SBML entry while the reports of its archive are built."""

    def __init__(self, source: Path | str, uid: str = "") -> None:
        """Read the document and build its report, without the link graph.

        Raises:
            MemoryError: if libsbml ran out of memory reading the source, an error of
                the memory as a `MemoryError` of python, see `isolation`.
            ValueError: if no model could be read from the source.
        """
        self.source = source
        start = time.perf_counter()
        self.info = SBMLDocumentInfo(SBMLDocumentInfo.read(source))
        log: libsbml.SBMLErrorLog = self.info.doc.getErrorLog()
        if log.contains(libsbml.XMLOutOfMemory):
            # libsbml catches the failed allocation of its parser and logs it
            raise MemoryError(f"libsbml ran out of memory:\n{log.toString()}")
        if self.info.doc.getModel() is None:
            # the message reaches the user, who can act on the errors of libsbml
            # but not on the temporary path the file was read from; `read_sbml`
            # logs that path for the server
            raise ValueError(
                "No SBML model could be read:\n"
                f"{self.info.doc.getErrorLog().toString()}"
            )
        self.info.build_report()
        self.elapsed = round(time.perf_counter() - start, 3)
        logger.info("report created for '%s' in %s s", uid, self.elapsed)

    def source_bytes(self) -> bytes:
        """Return original admitted XML bytes without rounding through an XML writer."""
        if isinstance(self.source, str):
            return self.source.encode()
        opener = gzip.open if _is_gzipped(self.source) else open
        with opener(self.source, "rb") as stream:
            content = stream.read(limits.MAX_CONTENT_SIZE + 1)
        if len(content) > limits.MAX_CONTENT_SIZE:
            raise ContentTooLargeError("The source exceeds its content size limit.")
        return content

    @property
    def link_source(self) -> LinkSource:
        """What the link graph of the report is built from."""
        return LinkSource(self.info.report, self.info.symbols, self.info.units_of_math)

    @property
    def report_entry(self) -> ReportEntry:
        """The report with the time it took to build."""
        return ReportEntry(
            report=self.info.report,
            debug=Debug(json_report_time=f"{self.elapsed} [s]"),
        )


def report_for_sbml(source: Path | str, uid: str = "") -> ReportEntry:
    """Create the report of a single SBML document.

    Args:
        source: path to an SBML file or SBML string.
        uid: identifier of the request, only used for logging.

    Raises:
        ValueError: if no model could be read from the source.
    """
    entry = _Entry(source, uid=uid)
    external = _resolve({SBML_LOCATION: entry}, checksums={}, locations=[])
    _link({SBML_LOCATION: entry}, external)
    _odes({SBML_LOCATION: entry}, validation.MAX_EXPANDED_ELEMENTS)
    return entry.report_entry


@dataclass
class _Read:
    """The SBML entries of a source, read and resolved against each other.

    Attributes:
        omex: the archive of the source, whose files are there while it is open.
        entries: the report of every SBML entry by its location, in the order
            of the manifest and then of the files next to a trusted file.
        external: the external model definitions resolved to the entries.
        uid: the identifier of the request, for the log.
    """

    omex: Omex
    entries: dict[str, _Entry]
    external: ExternalModels
    uid: str


@contextmanager
def _read(path: Path, trusted: bool) -> Generator[_Read]:
    """Read the SBML entries of a path and resolve them against each other.

    The archive of the path is extracted for the time of the context.

    Raises:
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    uid = uuid.uuid4().hex
    single = not Omex.is_omex(path)
    if not single and not trusted:
        _check_archive(path)
    with _omex_for_path(path, named=trusted, limited=not trusted) as omex:
        entries = {
            entry.location: _Entry(omex.get_path(entry.location), uid=uid)
            for entry in omex.manifest.entries
            if entry.is_sbml()
        }
        unreadable: list[str] = []
        if single and trusted:
            unreadable = _add_files_of_directory(omex, entries, path.parent, uid)

        locations = [entry.location for entry in omex.manifest.entries]
        checksums: dict[str, str] = {}
        if any(
            emd.md5 is not None
            for entry in entries.values()
            for emd in entry.info.report.external_model_definitions
        ):
            checksums = {
                location: _md5(omex.get_path(location)) for location in entries
            }
        external = _resolve(entries, checksums, [*locations, *unreadable])
        yield _Read(omex=omex, entries=entries, external=external, uid=uid)


def report_for_path(
    path: Path, trusted: bool = False, budget: int | None = None
) -> ReportResponse:
    """Create the reports of an SBML file or a COMBINE archive.

    Returns the archive manifest and one report per SBML entry of the archive.

    Args:
        path: the SBML file, plain or gzipped, or the COMBINE archive.
        trusted: the directory of the path was chosen by the operator or the
            user, so the files in it which the external model definitions of a
            single SBML file name are read as further entries. Never set for a
            path which holds the content of a request. The content of a path
            which is not trusted is read within the limits of `limits.py`.
        budget: the elements an entry may expand to for its equations, see
            `_odes`; by default `validation.MAX_EXPANDED_ELEMENTS`, which a
            child of a report gets in its job, since it does not see what a
            test changed in the server.

    Raises:
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    if budget is None:
        budget = validation.MAX_EXPANDED_ELEMENTS
    with _read(path, trusted) as read:
        _link(read.entries, read.external)
        _odes(read.entries, budget)
        manifest = Manifest(
            entries=[
                ManifestEntry(
                    location=entry.location,
                    format=str(entry.format),
                    master=entry.master,
                )
                for entry in read.omex.manifest.entries
            ]
        )
    reports = {location: entry.report_entry for location, entry in read.entries.items()}
    return ReportResponse(uid=read.uid, manifest=manifest, reports=reports)


@dataclass(frozen=True)
class ReportJob:
    """What the child process of a report reports.

    Attributes:
        path: the file of the source, which the server keeps until the child
            has ended.
        trusted: as for `report_for_path`.
        limits: the limits of `limits.py` an untrusted source is read within,
            read by the server when the report is asked for.
        budget: the elements an entry may expand to for its equations, read by
            the server when the report is asked for.
        parser: the server's selected parser, carried into forkserver children.
    """

    path: str
    trusted: bool
    limits: limits.ContentLimits
    budget: int
    parser: native.Parser = field(default_factory=native.preference)


# the key of the one result of a report, the gzipped json of the whole of it
_REPORT = "report"


def report_gzip(job: ReportJob) -> Iterator[tuple[str, bytes]]:
    """Report a source as gzipped JSON, what the child process runs.

    The source is read as `report_for_path` reads it, with the same trust and
    the same limits. The JSON is gzipped in the child, which keeps the largest
    report in a few megabytes of the pipe to the server instead of a hundred.

    Args:
        job: the source, the limits it is read within and the budget of its
            expanded size.

    Yields:
        The one pair of the key of a report and the gzipped JSON of its
        `ReportResponse`.

    Raises:
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    with job.limits.applied():
        raw = (
            None
            if job.trusted
            else native.report_json(Path(job.path), job.limits, job.budget, job.parser)
        )
        if raw is None:
            response = report_for_path(Path(job.path), job.trusted, job.budget)
            raw = response.model_dump_json(by_alias=True).encode()
    yield (_REPORT, gzip.compress(raw, compresslevel=REPORT_GZIP_LEVEL))


# the work of a request a child of `isolation.REPORT_BUDGET` does, of which a
# client reads in the sentence of an interruption: the report of a source, or
# its ODE system as a file to download. The names read in a log as well
Work = Literal["report", "ode system"]

# what a client reads of work its child did not finish, one sentence each, which
# names the work the client asked for and never the other
_INTERRUPTIONS: dict[Work, dict[isolation.Interruption, str]] = {
    "report": {
        "timeout": (
            "The report took longer than the {seconds:.0f} seconds a report may take."
        ),
        "memory": "The report needed more memory than the {memory} a report may use.",
        "crashed": (
            "The document could not be reported: the process which read it ended "
            "unexpectedly."
        ),
        "busy": "The server is busy with other reports, try again in a moment.",
    },
    "ode system": {
        "timeout": (
            "The ODE system took longer than the {seconds:.0f} seconds an ODE "
            "system may take."
        ),
        "memory": (
            "The ODE system needed more memory than the {memory} an ODE system may use."
        ),
        "crashed": (
            "The document could not be written as an ODE system: the process "
            "which read it ended unexpectedly."
        ),
        "busy": "The server is busy with other requests, try again in a moment.",
    },
}


def _memory_bound(memory: int) -> str:
    """The memory a child may use, as a client reads it.

    In GiB, which the 4 GiB of the budget are, and below one GiB in MiB, so
    that a bound a test lowered does not read as "0 GiB".

    Args:
        memory: the address space of a child, in bytes.

    Returns:
        The bound with its unit.
    """
    if memory < 1024**3:
        return f"{memory / 1024**2:.0f} MiB"
    return f"{memory / 1024**3:.0f} GiB"


class ReportInterruptedError(Exception):
    """Raised for work of the report budget the child process did not finish.

    The one error of the reports and of the ODE files, whose message is the
    sentence of its interruption for the work the client asked for.

    Attributes:
        interruption: why the child did not finish, see `isolation.IsolatedRun`.
        work: what it did not finish, the report of a source or its ODE system.
    """

    def __init__(
        self, interruption: isolation.Interruption, work: Work = "report"
    ) -> None:
        """Create the error of an interruption, whose sentence is its message."""
        super().__init__(
            _INTERRUPTIONS[work][interruption].format(
                seconds=isolation.REPORT_BUDGET.timeout,
                memory=_memory_bound(isolation.REPORT_BUDGET.memory),
            )
        )
        self.interruption = interruption
        self.work = work


def _log_isolated(
    kind: str, size: int, start: float, run: isolation.IsolatedRun | None
) -> None:
    """Log what a child of a source took, also for a run which raised.

    A run which raised is the one whose time a reader wants most, so it is
    logged where the call leaves, not where it returns.

    Args:
        kind: what the child built, as the log names it.
        size: the bytes of the content it built it from.
        start: the `time.perf_counter()` of the call.
        run: the run, None where it raised instead of returning one.
    """
    if run is None:
        outcome = ", failed"
    elif run.interruption is not None:
        outcome = f", {run.interruption}"
    else:
        outcome = ""
    logger.info(
        "%s of %s in %s s%s",
        kind,
        format_size(size),
        round(time.perf_counter() - start, 3),
        outcome,
    )


def report_gzip_for_bytes(content: bytes) -> bytes:
    """Create the gzipped JSON of the reports of untrusted content.

    The content is written to a temporary file like for `report_for_bytes`,
    which is there until the child has ended, and reported in a child process
    (`report_gzip` run by `isolation.run_isolated` with
    `isolation.REPORT_BUDGET`), bounded in time and memory.

    Args:
        content: an SBML file, plain or gzipped, or a COMBINE archive.

    Returns:
        The gzipped JSON of the `ReportResponse`, at `REPORT_GZIP_LEVEL`.

    Raises:
        ReportInterruptedError: if the child did not finish the report.
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content exceeds the limits.
    """
    start = time.perf_counter()
    run: isolation.IsolatedRun | None = None
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "model"
            path.write_bytes(content)
            job = ReportJob(
                path=str(path),
                trusted=False,
                limits=limits.ContentLimits.current(),
                budget=validation.MAX_EXPANDED_ELEMENTS,
            )
            run = isolation.run_isolated(report_gzip, job, isolation.REPORT_BUDGET)
    finally:
        _log_isolated("report", len(content), start, run)
    if run.interruption is not None or not run.results:
        # a child which ended without its one result ended abnormally
        raise ReportInterruptedError(run.interruption or "crashed")
    return run.results[0][1]


@dataclass(frozen=True)
class SourceJob:
    """What the child process of a validation validates.

    Attributes:
        path: the file of the source, which the server keeps until the child
            has ended.
        trusted: as for `report_for_path`.
        budget: the elements an entry with submodel instances may expand to,
            read by the server when the validation is asked for.
        limits: the limits of `limits.py` an untrusted source is read within,
            read by the server when the validation is asked for.
    """

    path: str
    trusted: bool
    budget: int
    limits: limits.ContentLimits


# the key of the result which names the entries, which no location is
_LOCATIONS = ""


def _expanded_size(entries: Mapping[str, _Entry], location: str) -> int | None:
    """The elements an entry of a source expands to by its comp submodels.

    Its own elements and those its submodel instances add along every level
    (`validation.instantiated_elements`), which is what the comp validator
    instantiates when it checks the entry and what the flattening of its ODE
    system builds, each of them in the memory of one process. An entry without
    a submodel instance expands to nothing and is bounded by no budget of the
    expanded size, however many elements of its own it has.

    Args:
        entries: the report of every entry of the source by its location.
        location: the location of the entry.

    Returns:
        The expanded size of an entry with submodel instances, None for an
        entry without one.
    """
    instantiated = instantiated_elements(
        {loc: entry.info.report for loc, entry in entries.items()},
        {loc: entry.info.elements for loc, entry in entries.items()},
        location,
    )
    if instantiated == 0:
        return None
    return sum(entries[location].info.elements.values()) + instantiated


def validate_source(job: SourceJob) -> Iterator[tuple[str, Any]]:
    """Read a source and validate its entries, what the child process runs.

    The source is read as `report_for_path` reads it, with the same trust and
    the same limits, so that the pks of the issues are those of its report.
    An entry with comp submodel instances which expands to more than
    `job.budget` elements, its own and those its submodels instantiate, is
    skipped with the issues of reading it. As soon as one submodel is
    instantiated, the comp validator checks the whole flattened model, whose
    cost grows faster than its size; a document without instances is checked
    in a time linear in its size, which the timeout bounds.

    Args:
        job: the source and the budget.

    Yields:
        First `("", locations)`, the entries in their order, then the location
        and the `EntryValidation` of every entry, in that order.

    Raises:
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    with job.limits.applied(), _read(Path(job.path), job.trusted) as read:
        yield _LOCATIONS, list(read.entries)
        documents = ReportDocuments(
            {location: entry.info.doc for location, entry in read.entries.items()}
        )
        for location, entry in read.entries.items():
            size = _expanded_size(read.entries, location)
            if size is not None and size > job.budget:
                logger.warning(
                    "'%s' is not validated: it expands to %s elements, more than %s",
                    location,
                    size,
                    job.budget,
                )
                yield (
                    location,
                    EntryValidation(
                        issues=issues_of(entry.info.doc, entry.info.positions),
                        skipped="expandedSize",
                    ),
                )
                continue
            issues = validate(entry.info.doc, entry.info.positions, documents, location)
            yield location, EntryValidation(issues=issues)


def validation_for_path(path: Path, trusted: bool = False) -> ValidationResponse:
    """Validate the SBML entries of an SBML file or a COMBINE archive.

    Every touch of libsbml, from reading the source on, is in a child process
    (`validate_source` run by `isolation.run_isolated` with
    `isolation.VALIDATION_BUDGET`), bounded in time and memory; the path has to
    be there until this returns.

    Args:
        path: the SBML file, plain or gzipped, or the COMBINE archive.
        trusted: as for `report_for_path`.

    Returns:
        The validation of every entry; when it stopped early, its reason as
        the reason of the response and of every entry it did not reach.

    Raises:
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    start = time.perf_counter()
    job = SourceJob(
        path=str(path),
        trusted=trusted,
        budget=validation.MAX_EXPANDED_ELEMENTS,
        limits=limits.ContentLimits.current(),
    )
    run = isolation.run_isolated(validate_source, job, isolation.VALIDATION_BUDGET)
    locations: list[str] = []
    validated: dict[str, EntryValidation] = {}
    for key, value in run.results:
        if key == _LOCATIONS:
            locations = value
        else:
            validated[key] = value
    entries = {
        location: validated.get(location, EntryValidation(skipped=run.interruption))
        for location in locations
    }
    logger.info(
        "validation of '%s' in %s s%s",
        path.name,
        round(time.perf_counter() - start, 3),
        f", {run.interruption}" if run.interruption else "",
    )
    return ValidationResponse(entries=entries, skipped=run.interruption)


def _resolve(
    entries: dict[str, _Entry], checksums: dict[str, str], locations: list[str]
) -> ExternalModels:
    """Resolve the external model definitions of the entries against each other."""
    reports = {location: entry.info.report for location, entry in entries.items()}
    external = ExternalModels(reports, checksums=checksums, locations=locations)
    external.resolve_all()
    return external


def _link(entries: dict[str, _Entry], external: ExternalModels) -> None:
    """Build the graph of every entry, along the resolved external models."""
    build_link_graphs(
        {location: entry.link_source for location, entry in entries.items()}, external
    )


def _odes(entries: dict[str, _Entry], budget: int) -> None:
    """Build the ODE system of every entry, its submodels flattened within the report.

    An external model definition of an entry resolves to another entry of the
    report alone, as in the validation, see `odes.ode_system`.

    An entry which expands by its comp submodels to more than `budget`
    elements (`_expanded_size`) keeps its elements and gets no equations, with
    `_NOT_FLATTENED` as its `ode_error`: the shared Rust expansion holds every
    instantiated element into one model, so its memory grows with the expanded
    size and not with the size of the document, and a document of a few
    kilobytes whose submodels fan out reaches beyond every bound a child of
    `isolation.REPORT_BUDGET` could have, while the rest of its report costs
    what its own elements cost. The budget is the one the comp validator is
    gated by, which instantiates the same submodels, so a document the
    validation skips for its expanded size is the document whose equations are
    not built.

    Args:
        entries: the report of every entry by its location.
        budget: the elements an entry may expand to for its equations.
    """
    documents = ReportDocuments(
        {location: entry.info.doc for location, entry in entries.items()},
        sources={location: entry.source_bytes for location, entry in entries.items()},
    )
    for location, entry in entries.items():
        report = entry.info.report
        main = next((m for m in report.models if m.kind == "model"), None)
        if main is None:
            continue
        size = _expanded_size(entries, location)
        if size is not None and size > budget:
            logger.warning(
                "no equations of '%s': it expands to %s elements, more than %s",
                location,
                size,
                budget,
            )
            report.ode_error = _NOT_FLATTENED.format(size=size, budget=budget)
            continue
        report.ode_system, report.ode_error = ode_system(
            entry.info.doc, main, documents, location, budget
        )


def _md5(path: Path) -> str:
    """The md5 of a file, which an external model definition states (comp §3.3.2)."""
    with path.open("rb") as f:
        return hashlib.file_digest(
            f, lambda: hashlib.md5(usedforsecurity=False)
        ).hexdigest()


def _add_files_of_directory(
    omex: Omex, entries: dict[str, _Entry], directory: Path, uid: str
) -> list[str]:
    """Add the files the external model definitions name as entries of the archive.

    The master entry stands for the file it was read from, so a source is
    resolved against its location the way it is inside an archive, and what it
    names is a file below `directory`. A file which is read names files of its
    own. A source which leaves the directory, by its path or through a symbolic
    link, is not read, and neither is a file without a readable model, whose
    location is returned so that the report can say that it is there.
    """
    root = directory.resolve()
    unreadable: list[str] = []
    seen = {normalize_location(location) for location in entries}
    pending = list(entries)
    while pending:
        location = pending.pop(0)
        for emd in entries[location].info.report.external_model_definitions:
            normalized = resolve_source(location, emd.source)
            if normalized is None or normalized in seen:
                continue
            seen.add(normalized)
            path = (root / normalized).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                continue
            added = f"./{normalized}"
            try:
                entry = _Entry(path, uid=uid)
            except ValueError:
                logger.warning("'%s' next to the model holds no SBML model", added)
                unreadable.append(added)
                continue
            omex.add_entry(
                entry_path=path,
                entry=OmexManifestEntry(
                    location=added, format=EntryFormat.SBML, master=False
                ),
            )
            entries[added] = entry
            pending.append(added)
    return unreadable


@dataclass(frozen=True)
class OdeFile:
    """The ODE system of a model in a format of sbmlsim-core, as a file.

    Attributes:
        filename: the name of the file, the id of the model with the suffix of the
            format, `BIOMD0000000012.py`
        content: the code or the document
    """

    filename: str
    content: str


def ode_for_path(
    path: Path,
    fmt: str,
    location: str | None = None,
    trusted: bool = False,
    simulator: bool = False,
    budget: int | None = None,
) -> OdeFile:
    """Write the ODE system of the model of an SBML entry in a format of sbmlsim-core.

    The source is read like for its report, and an external model definition is
    resolved to the entries of the report alone, see `odes.ode_system`. Code is
    the ODE system alone (the initial values, the rates of change and the assigned
    values), without the simulator of sbmlsim-core unless `simulator` is set; a
    document is standalone with the ids as symbols, the defaults of sbmlsim-core.

    Args:
        path: an SBML file or COMBINE archive.
        fmt: the format, a key of `sbmlsim_core.ODE_FORMATS`.
        location: the SBML entry of an archive, by default its master entry or
            the first one.
        trusted: whether the files next to a single SBML file are read, see
            `report_for_path`.
        simulator: whether code holds the simulator of sbmlsim-core, which integrates
            the model.
        budget: the elements the entry may expand to, as for `report_for_path`;
            an entry beyond it is not flattened, here as in a report.

    Raises:
        ValueError: for an unknown format or location, a source without a model,
            a model which expands beyond `budget` elements, or a model sbmlsim-core
            cannot write in the format.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    import sbmlsim_core

    format_ = sbmlsim_core.ODE_FORMATS.get(fmt)
    if format_ is None:
        raise ValueError(
            f"The format '{fmt}' is none of {', '.join(sorted(sbmlsim_core.ODE_FORMATS))}."
        )
    if budget is None:
        budget = validation.MAX_EXPANDED_ELEMENTS
    with _read(path, trusted) as read:
        if location is None:
            masters = [e.location for e in read.omex.manifest.entries if e.master]
            location = next(
                (m for m in masters if m in read.entries), next(iter(read.entries))
            )
        entry = read.entries.get(location)
        if entry is None:
            raise ValueError(f"The source has no SBML entry '{location}'.")
        size = _expanded_size(read.entries, location)
        if size is not None and size > budget:
            raise ValueError(_NOT_FLATTENED.format(size=size, budget=budget))
        documents = ReportDocuments(
            {loc: e.info.doc for loc, e in read.entries.items()},
            sources={loc: e.source_bytes for loc, e in read.entries.items()},
        )
        doc = entry.info.doc
        system = analyse(doc, documents, location, budget)
        if format_.kind == "code":
            content = system.render(fmt, simulator=simulator)
        else:
            content = system.render(fmt)
    model_id = doc.getModel().getId() or "model"
    return OdeFile(filename=f"{model_id}{format_.suffixes[0]}", content=content)


@dataclass(frozen=True)
class OdeJob:
    """What the child process of an ODE download writes.

    Attributes:
        path: the file of the source, which the server keeps until the child
            has ended.
        trusted: as for `report_for_path`.
        limits: the limits of `limits.py` an untrusted source is read within,
            read by the server when the file is asked for.
        fmt: the format, a key of `sbmlsim_core.ODE_FORMATS`.
        location: the SBML entry of an archive, by default its master entry or
            the first one.
        budget: the elements the entry may expand to, read by the server when
            the file is asked for.
    """

    path: str
    trusted: bool
    limits: limits.ContentLimits
    fmt: str
    location: str | None
    budget: int


# the key of the one result of an ODE download, the file of the whole system
_ODE = "ode"


def ode_source(job: OdeJob) -> Iterator[tuple[str, OdeFile]]:
    """Write the ODE system of a source, what the child process runs.

    The source is read as `ode_for_path` reads it, with the same trust and the
    same limits. The file holds the system of one model, which is small next to
    a report, so it crosses the boundary to the server pickled, as the results
    of a validation do.

    Args:
        job: the source, the format of the file, the limits it is read within
            and the budget of its expanded size.

    Yields:
        The one pair of the key of an ODE file and the file.

    Raises:
        ValueError: for an unknown format or location, a source without a model,
            a model which expands beyond the budget of the job, or a model
            sbmlsim-core cannot write in the format.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    with job.limits.applied():
        yield (
            _ODE,
            ode_for_path(
                Path(job.path),
                job.fmt,
                job.location,
                job.trusted,
                budget=job.budget,
            ),
        )


def ode_for_bytes(content: bytes, fmt: str, location: str | None = None) -> OdeFile:
    """Write the ODE system of untrusted content in a format of sbmlsim-core.

    The content is written to a temporary file like for `report_gzip_for_bytes`,
    which is there until the child has ended, and read in a child process
    (`ode_source` run by `isolation.run_isolated` with
    `isolation.REPORT_BUDGET`, which the reports and the ODE files of the
    requests share), bounded in time and memory.

    Args:
        content: an SBML file, plain or gzipped, or a COMBINE archive.
        fmt: the format, a key of `sbmlsim_core.ODE_FORMATS`.
        location: the SBML entry of an archive, by default its master entry or
            the first one.

    Returns:
        The ODE system of the model of the entry, as a file.

    Raises:
        ReportInterruptedError: if the child did not finish the file.
        ValueError: for an unknown format or location, content without a model,
            a model which expands beyond `validation.MAX_EXPANDED_ELEMENTS`
            elements, or a model sbmlsim-core cannot write in the format.
        ContentTooLargeError: if the content exceeds the limits.
    """
    start = time.perf_counter()
    run: isolation.IsolatedRun | None = None
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "model"
            path.write_bytes(content)
            job = OdeJob(
                path=str(path),
                trusted=False,
                limits=limits.ContentLimits.current(),
                fmt=fmt,
                location=location,
                budget=validation.MAX_EXPANDED_ELEMENTS,
            )
            run = isolation.run_isolated(ode_source, job, isolation.REPORT_BUDGET)
    finally:
        _log_isolated(f"ode system ({fmt})", len(content), start, run)
    if run.interruption is not None or not run.results:
        # a child which ended without its one result ended abnormally
        raise ReportInterruptedError(run.interruption or "crashed", "ode system")
    return run.results[0][1]


def report_for_bytes(content: bytes) -> ReportResponse:
    """Create the reports of the content of an SBML file or COMBINE archive.

    The content is written to a temporary file, so that archives (zip files)
    as well as plain or gzipped SBML are handled by `report_for_path`.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "model"
        path.write_bytes(content)
        return report_for_path(path)


def validation_for_bytes(content: bytes) -> ValidationResponse:
    """Validate the content of an SBML file or COMBINE archive.

    The content is written to a temporary file like for `report_for_bytes`,
    which is there until the validation has ended.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "model"
        path.write_bytes(content)
        return validation_for_path(path)


def _omex_for_path(path: Path, named: bool = False, limited: bool = False) -> Omex:
    """Open the archive at path, or wrap the SBML file at path in a new archive.

    Gzipped SBML is decompressed, libsbml only detects compression by the file
    extension which is lost in the archive. With `named` the entry of a single
    file carries the name of that file, which is what the sources of the files
    next to it are resolved against. With `limited` the decompressed SBML may
    not exceed `MAX_CONTENT_SIZE`.

    The archive is extracted into a temporary directory, which the caller
    removes by using the archive as a context manager.
    """
    if Omex.is_omex(path):
        return Omex.from_omex(path)

    location = SBML_LOCATION
    if named:
        name = path.name.removesuffix(".gz") if _is_gzipped(path) else path.name
        location = f"./{name}"

    with ExitStack() as stack:
        omex = stack.enter_context(Omex())
        with tempfile.TemporaryDirectory() as tmp_dir:
            if _is_gzipped(path):
                sbml_path = Path(tmp_dir) / "model.xml"
                _gunzip(path, sbml_path, limits.MAX_CONTENT_SIZE if limited else None)
            else:
                sbml_path = path

            # the entry is copied into the archive
            omex.add_entry(
                entry_path=sbml_path,
                entry=OmexManifestEntry(
                    location=location, format=EntryFormat.SBML, master=True
                ),
            )
        # the archive is the caller's, who removes its directory
        stack.pop_all()
    return omex


def _gunzip(source: Path, target: Path, limit: int | None) -> None:
    """Decompress a gzipped file in chunks, up to `limit` bytes if one is given.

    Raises:
        ContentTooLargeError: if the decompressed content exceeds the limit.
    """
    size = 0
    with gzip.open(source, "rb") as f_in, target.open("wb") as f_out:
        while chunk := f_in.read(CHUNK_SIZE):
            size += len(chunk)
            if limit is not None and size > limit:
                raise ContentTooLargeError(
                    "The decompressed model is larger than the limit of "
                    f"{format_size(limit)}."
                )
            f_out.write(chunk)


def _check_archive(path: Path) -> None:
    """Refuse an archive beyond the limits before it is extracted.

    The sizes are the ones the archive states, which bound what is extracted:
    `zipfile` reads no more of an entry than its stated size.

    Raises:
        ContentTooLargeError: if the archive has more than `MAX_ARCHIVE_ENTRIES`
            entries, more than `MAX_CONTENT_SIZE` uncompressed or an entry above
            `COMPRESSION_RATIO_MIN_SIZE` compressed more than
            `MAX_COMPRESSION_RATIO` times.
    """
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
    if len(infos) > limits.MAX_ARCHIVE_ENTRIES:
        raise ContentTooLargeError(
            f"The archive has more than {limits.MAX_ARCHIVE_ENTRIES} entries."
        )
    size = sum(info.file_size for info in infos)
    if size > limits.MAX_CONTENT_SIZE:
        raise ContentTooLargeError(
            "The uncompressed archive is larger than the limit of "
            f"{format_size(limits.MAX_CONTENT_SIZE)}."
        )
    for info in infos:
        if (
            info.file_size > limits.COMPRESSION_RATIO_MIN_SIZE
            and info.file_size > limits.MAX_COMPRESSION_RATIO * info.compress_size
        ):
            raise ContentTooLargeError(
                f"The entry '{info.filename}' of the archive is compressed more "
                f"than {limits.MAX_COMPRESSION_RATIO} times."
            )


def _is_gzipped(path: Path) -> bool:
    """Check the magic bytes of the file for gzip."""
    with path.open("rb") as f:
        return f.read(len(GZIP_MAGIC)) == GZIP_MAGIC
