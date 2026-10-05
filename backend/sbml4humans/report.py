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

The validation of libsbml is not part of the report: `validation_for_path`
reads the entries of a source the same way, without their link graph, and
checks them in a child process (`isolation.py`), so that the report is answered
as fast as it is built and its validation when it is finished.
"""

import gzip
import hashlib
import logging
import tempfile
import time
import uuid
import zipfile
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path

from pymetadata.omex import EntryFormat, Omex
from pymetadata.omex import ManifestEntry as OmexManifestEntry

from sbml4humans import isolation, limits, validation
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
    ValidationIssue,
    ValidationResponse,
)
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.validation import (
    ValidationJob,
    expanded_size,
    issues_of,
    validate_entries,
)


logger = logging.getLogger(__name__)

# location of a single SBML file in the archive created for it
SBML_LOCATION = "./model.xml"
GZIP_MAGIC = b"\x1f\x8b"
# the bytes decompressed at a time
CHUNK_SIZE = 1024 * 1024  # [byte]


class _Entry:
    """The report of one SBML entry while the reports of its archive are built."""

    def __init__(self, source: Path | str, uid: str = "") -> None:
        """Read the document and build its report, without the link graph.

        Raises:
            ValueError: if no model could be read from the source.
        """
        start = time.perf_counter()
        self.info = SBMLDocumentInfo(SBMLDocumentInfo.read(source))
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
def _read(path: Path, trusted: bool) -> Iterator[_Read]:
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


def report_for_path(path: Path, trusted: bool = False) -> ReportResponse:
    """Create the reports of an SBML file or a COMBINE archive.

    Returns the archive manifest and one report per SBML entry of the archive.

    Args:
        path: the SBML file, plain or gzipped, or the COMBINE archive.
        trusted: the directory of the path was chosen by the operator or the
            user, so the files in it which the external model definitions of a
            single SBML file name are read as further entries. Never set for a
            path which holds the content of a request. The content of a path
            which is not trusted is read within the limits of `limits.py`.

    Raises:
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
    """
    with _read(path, trusted) as read:
        _link(read.entries, read.external)
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


def validation_for_path(path: Path, trusted: bool = False) -> ValidationResponse:
    """Validate the SBML entries of an SBML file or a COMBINE archive.

    The entries are read as `report_for_path` reads them, with the same trust
    and the same limits, so that the pks of the issues are those of the report
    of the path. An entry whose comp submodels expand it to more than
    `MAX_EXPANDED_ELEMENTS` elements is skipped with the issues of reading it,
    the others are checked in a child process (`isolation.run_isolated`),
    bounded in time and memory, which reads the files of the archive while it
    is extracted.

    Args:
        path: the SBML file, plain or gzipped, or the COMBINE archive.
        trusted: as for `report_for_path`.

    Raises:
        ValueError: if no model could be read from an SBML entry.
        ContentTooLargeError: if the content of an untrusted path exceeds the
            limits.
        ValidationProcessError: if the child process ended unexpectedly.
    """
    with _read(path, trusted) as read:
        reports = {
            location: entry.info.report for location, entry in read.entries.items()
        }
        elements = {
            location: entry.info.elements for location, entry in read.entries.items()
        }
        skipped: dict[str, EntryValidation] = {}
        targets: dict[str, validation.ElementPositions] = {}
        budget = validation.MAX_EXPANDED_ELEMENTS
        for location, entry in read.entries.items():
            size = expanded_size(reports, elements, location)
            # a flat document is checked in a time linear in its size, which
            # the timeout bounds, so only instances count against the budget
            if size > budget and size > sum(entry.info.elements.values()):
                logger.warning(
                    "'%s' is not validated: it expands to %s elements, more than %s",
                    location,
                    size,
                    budget,
                )
                skipped[location] = EntryValidation(
                    issues=issues_of(entry.info.doc, entry.info.positions),
                    skipped="expandedSize",
                )
            else:
                targets[location] = entry.info.positions
        results: dict[str, list[ValidationIssue] | isolation.Interruption] = {}
        if targets:
            start = time.perf_counter()
            job = ValidationJob(
                paths={
                    location: str(read.omex.get_path(location))
                    for location in read.entries
                },
                targets=targets,
            )
            results = isolation.run_isolated(validate_entries, job, list(targets))
            logger.info(
                "validation of '%s' in %s s",
                read.uid,
                round(time.perf_counter() - start, 3),
            )
    entries: dict[str, EntryValidation] = {}
    for location in read.entries:
        if location in skipped:
            entries[location] = skipped[location]
            continue
        result = results[location]
        if isinstance(result, list):
            entries[location] = EntryValidation(issues=result)
        else:
            entries[location] = EntryValidation(skipped=result)
    return ValidationResponse(entries=entries)


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
