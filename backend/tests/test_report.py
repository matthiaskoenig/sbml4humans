"""Tests of the report creation."""

import gzip
from pathlib import Path

import pytest
from sbmlutils.resources import (
    API_EXAMPLES_MODEL,
    API_EXAMPLES_OMEX,
    BIOMODELS_CURATED_PATH,
    OMEX_ICGMODEL,
    REPRESSILATOR_SBML,
    sbml_paths_idfn,
)

from sbml4humans.report import report_for_bytes, report_for_path, report_for_sbml


BIOMODELS = sorted(BIOMODELS_CURATED_PATH.glob("BIOMD*.omex"))[:10]
PATHS = API_EXAMPLES_OMEX + API_EXAMPLES_MODEL + BIOMODELS


def _check_report(data: dict) -> None:
    """Check the structure of the report data of a path."""
    assert set(data) == {"uid", "manifest", "reports"}
    assert len(data["uid"]) == 32
    assert data["manifest"]["entries"]
    assert data["reports"]
    for location, report in data["reports"].items():
        assert location.startswith("./")
        assert set(report) == {"report", "debug"}
        assert report["report"]["doc"]
        assert report["debug"]["jsonReportTime"].endswith(" [s]")


@pytest.mark.parametrize("path", PATHS, ids=sbml_paths_idfn)
def test_report_for_path(path: Path) -> None:
    """Report data is created for all examples."""
    assert path.is_file()
    _check_report(report_for_path(path))


def test_report_for_sbml_file() -> None:
    """A single SBML file is wrapped in an archive with one master model."""
    data = report_for_path(REPRESSILATOR_SBML)
    assert list(data["reports"]) == ["./model.xml"]
    assert data["reports"]["./model.xml"]["report"]["doc"]


def test_report_for_omex_has_all_sbml_entries() -> None:
    """Every SBML entry of an archive gets its own report."""
    data = report_for_path(OMEX_ICGMODEL)
    assert len(data["reports"]) == 3
    assert "./models/icg_body.xml" in data["reports"]


def test_report_for_sbml_string() -> None:
    """Report data is created from an SBML string."""
    data = report_for_sbml(REPRESSILATOR_SBML.read_text(encoding="utf-8"))
    assert data["report"]["doc"]
    assert data["debug"]["jsonReportTime"].endswith(" [s]")


def test_report_for_bytes_sbml() -> None:
    """Report data is created from the bytes of an SBML file."""
    _check_report(report_for_bytes(REPRESSILATOR_SBML.read_bytes()))


def test_report_for_bytes_omex() -> None:
    """Report data is created from the (binary) bytes of an archive."""
    data = report_for_bytes(OMEX_ICGMODEL.read_bytes())
    _check_report(data)
    assert len(data["reports"]) == 3


def test_report_for_bytes_gzipped_sbml() -> None:
    """Report data is created from gzipped SBML."""
    data = report_for_bytes(gzip.compress(REPRESSILATOR_SBML.read_bytes()))
    _check_report(data)
    assert list(data["reports"]) == ["./model.xml"]


def test_report_for_bytes_invalid() -> None:
    """Content which is neither SBML nor an archive raises."""
    with pytest.raises(ValueError, match="No SBML model could be read"):
        report_for_bytes(b"this is not a model")


def test_report_for_sbml_without_model() -> None:
    """An SBML document without model raises with the libsbml errors."""
    with pytest.raises(ValueError, match="No SBML model"):
        report_for_sbml('<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core"/>')


def test_uid_differs_between_reports() -> None:
    """Every report gets its own uid."""
    uid1 = report_for_path(REPRESSILATOR_SBML)["uid"]
    uid2 = report_for_path(REPRESSILATOR_SBML)["uid"]
    assert uid1 != uid2
