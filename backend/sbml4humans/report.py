"""Report data for SBML models and COMBINE archives.

The report of a model is the `Report` created by `SBMLDocumentInfo`. A single
SBML file is wrapped in a COMBINE archive with one master model, so that the
frontend always receives an archive manifest with one report per SBML entry.
"""

import gzip
import logging
import tempfile
import time
import uuid
from pathlib import Path

from pymetadata.omex import EntryFormat, ManifestEntry, Omex

from sbml4humans.model import Debug, ReportEntry, ReportResponse
from sbml4humans.sbmlinfo import SBMLDocumentInfo


logger = logging.getLogger(__name__)

# location of a single SBML file in the archive created for it
SBML_LOCATION = "./model.xml"
GZIP_MAGIC = b"\x1f\x8b"


def report_for_sbml(source: Path | str, uid: str = "") -> ReportEntry:
    """Create the report of a single SBML document.

    Args:
        source: path to an SBML file or SBML string.
        uid: identifier of the request, only used for logging.

    Raises:
        ValueError: if no model could be read from the source.
    """
    start = time.perf_counter()
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(source))
    if info.doc.getModel() is None:
        raise ValueError(
            f"No SBML model could be read from '{source}':\n"
            f"{info.doc.getErrorLog().toString()}"
        )
    report = info.build()
    elapsed = round(time.perf_counter() - start, 3)
    logger.info("report created for '%s' in %s s", uid, elapsed)
    return ReportEntry(report=report, debug=Debug(json_report_time=f"{elapsed} [s]"))


def report_for_path(path: Path) -> ReportResponse:
    """Create the reports of an SBML file or a COMBINE archive.

    Returns the archive manifest and one report per SBML entry of the archive.
    """
    uid = uuid.uuid4().hex
    omex = _omex_for_path(path)
    reports = {
        entry.location: report_for_sbml(omex.get_path(entry.location), uid=uid)
        for entry in omex.manifest.entries
        if entry.is_sbml()
    }
    return ReportResponse(uid=uid, manifest=omex.manifest.model_dump(), reports=reports)


def report_for_bytes(content: bytes) -> ReportResponse:
    """Create the reports of the content of an SBML file or COMBINE archive.

    The content is written to a temporary file, so that archives (zip files)
    as well as plain or gzipped SBML are handled by `report_for_path`.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "model"
        path.write_bytes(content)
        return report_for_path(path)


def _omex_for_path(path: Path) -> Omex:
    """Open the archive at path, or wrap the SBML file at path in a new archive.

    Gzipped SBML is decompressed, libsbml only detects compression by the file
    extension which is lost in the archive.
    """
    if Omex.is_omex(path):
        return Omex.from_omex(path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        if _is_gzipped(path):
            sbml_path = Path(tmp_dir) / "model.xml"
            sbml_path.write_bytes(gzip.decompress(path.read_bytes()))
        else:
            sbml_path = path

        # the entry is copied into the archive
        omex = Omex()
        omex.add_entry(
            entry_path=sbml_path,
            entry=ManifestEntry(
                location=SBML_LOCATION, format=EntryFormat.SBML, master=True
            ),
        )
    return omex


def _is_gzipped(path: Path) -> bool:
    """Check the magic bytes of the file for gzip."""
    with path.open("rb") as f:
        return f.read(len(GZIP_MAGIC)) == GZIP_MAGIC
