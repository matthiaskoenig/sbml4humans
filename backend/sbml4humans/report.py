"""Rust source operations behind the FastAPI worker and transport boundary.

Python admits requests and preserves worker deadlines, memory limits,
cancellation and completed entry results. Rust reads, resolves, validates,
renders, serializes and compresses SBML reports and ODE exports.
"""

import json
import logging
import tempfile
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sbml4humans import isolation, limits, native
from sbml4humans.limits import format_size
from sbml4humans.model import (
    EntryValidation,
    ReportEntry,
    ReportResponse,
    ValidationResponse,
)


logger = logging.getLogger(__name__)

# location of a single SBML file in the archive created for it
SBML_LOCATION = "./model.xml"
# the level the JSON of a report is gzipped at, by the child of a report and by
# the api. A moderate level: the reports compress about 20 fold already at this
# level, and a higher one costs time on every large report for a few percent
REPORT_GZIP_LEVEL = 5


def report_for_path(
    path: Path,
    trusted: bool = False,
    budget: int | None = None,
    *,
    source_entry: str | None = None,
) -> ReportResponse:
    """Build a report through Rust, with confined trusted example companions."""
    raw = native.report_json(
        path,
        limits.ContentLimits.current(),
        limits.MAX_EXPANDED_ELEMENTS if budget is None else budget,
        trusted=trusted,
        source_entry=source_entry,
    )
    return ReportResponse.model_validate_json(raw)


def report_gzip_for_path(
    path: Path, trusted: bool = False, *, source_entry: str | None = None
) -> bytes:
    """Receive final compressed bytes for a trusted example or local path."""
    return native.report_json(
        path,
        limits.ContentLimits.current(),
        limits.MAX_EXPANDED_ELEMENTS,
        trusted=trusted,
        source_entry=source_entry,
        gzip=True,
    )


def report_for_sbml(source: Path | str, uid: str = "") -> ReportEntry:
    """Report standalone source content or a path through the Rust reader."""
    response = (
        report_for_bytes(source.encode())
        if isinstance(source, str) and "<sbml" in source
        else report_for_path(Path(source))
    )
    return next(iter(response.reports.values()))


@dataclass(frozen=True)
class ReportJob:
    """What the child process of a report reports.

    Attributes:
        path: the file of the source, which the server keeps until the child
            has ended.
        trusted: as for `report_for_path`.
        source_entry: a selected trusted example entry, without archive extraction.
        limits: the limits of `limits.py` an untrusted source is read within,
            read by the server when the report is asked for.
        budget: the elements an entry may expand to for its equations, read by
            the server when the report is asked for.
    """

    path: str
    trusted: bool
    limits: limits.ContentLimits
    budget: int
    source_entry: str | None = None


# the key of the one result of a report, the gzipped json of the whole of it
_REPORT = "report"


def report_gzip(job: ReportJob) -> Iterator[tuple[str, bytes]]:
    """Serialize and compress the report in Rust before crossing the worker pipe."""
    with job.limits.applied():
        content = native.report_json(
            Path(job.path),
            job.limits,
            job.budget,
            trusted=job.trusted,
            source_entry=job.source_entry,
            gzip=True,
        )
    yield _REPORT, content


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
                budget=limits.MAX_EXPANDED_ELEMENTS,
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
        source_entry: a selected trusted example entry, without archive extraction.
        budget: the elements an entry with submodel instances may expand to,
            read by the server when the validation is asked for.
        limits: the limits of `limits.py` an untrusted source is read within,
            read by the server when the validation is asked for.
    """

    path: str
    trusted: bool
    budget: int
    limits: limits.ContentLimits
    source_entry: str | None = None


# the key of the result which names the entries, which no location is
_LOCATIONS = ""


def validate_source(job: SourceJob) -> Iterator[tuple[str, Any]]:
    """Prepare in Rust and stream completed validations under the worker budget."""
    with job.limits.applied():
        session = native.validation_source(
            Path(job.path),
            job.limits,
            job.budget,
            trusted=job.trusted,
            source_entry=job.source_entry,
        )
        locations = session.locations
        yield _LOCATIONS, locations
        for location in locations:
            yield (
                location,
                EntryValidation.model_validate_json(session.entry_json(location)),
            )


def validation_for_path(
    path: Path, trusted: bool = False, *, source_entry: str | None = None
) -> ValidationResponse:
    """Validate the SBML entries of an SBML file or a COMBINE archive.

    Every touch of libsbml, from reading the source on, is in a child process
    (`validate_source` run by `isolation.run_isolated` with
    `isolation.VALIDATION_BUDGET`), bounded in time and memory; the path has to
    be there until this returns.

    Args:
        path: the SBML file, plain or gzipped, or the COMBINE archive.
        trusted: as for `report_for_path`.
        source_entry: a selected trusted example entry, without archive extraction.

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
        source_entry=source_entry,
        budget=limits.MAX_EXPANDED_ELEMENTS,
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
    *,
    source_entry: str | None = None,
) -> OdeFile:
    """Select and export an admitted model through the shared Rust generator."""
    content = native.ode_json(
        path,
        fmt,
        location,
        limits.ContentLimits.current(),
        limits.MAX_EXPANDED_ELEMENTS if budget is None else budget,
        trusted=trusted,
        simulator=simulator,
        source_entry=source_entry,
    )
    return OdeFile(**json.loads(content))


@dataclass(frozen=True)
class OdeJob:
    """What the child process of an ODE download writes.

    Attributes:
        path: the file of the source, which the server keeps until the child
            has ended.
        trusted: as for `report_for_path`.
        source_entry: a selected trusted example entry, without archive extraction.
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
    source_entry: str | None = None


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
                source_entry=job.source_entry,
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
            a model which expands beyond `limits.MAX_EXPANDED_ELEMENTS`
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
                budget=limits.MAX_EXPANDED_ELEMENTS,
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
