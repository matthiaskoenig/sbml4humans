"""Tests of the report creation."""

import gzip
from pathlib import Path

import pytest

from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_bytes, report_for_path, report_for_sbml
from sbml4humans.resources import (
    API_EXAMPLES_MODEL,
    API_EXAMPLES_OMEX,
    BIOMODELS_CURATED_PATH,
    OMEX_ICGMODEL,
    REPRESSILATOR_SBML,
)


BIOMODELS = sorted(BIOMODELS_CURATED_PATH.glob("BIOMD*.omex"))[:10]
PATHS = API_EXAMPLES_OMEX + API_EXAMPLES_MODEL + BIOMODELS


def _check_report(response: ReportResponse) -> None:
    """Check the structure of the report response of a path."""
    assert len(response.uid) == 32
    assert response.manifest.entries
    assert all(e.location and e.format for e in response.manifest.entries)
    assert len([e for e in response.manifest.entries if e.master]) <= 1
    assert response.reports
    for location, entry in response.reports.items():
        assert location.startswith("./")
        assert entry.report.document.level in {1, 2, 3}
        assert entry.debug.json_report_time.endswith(" [s]")


@pytest.mark.parametrize("path", PATHS, ids=lambda path: path.name)
def test_report_for_path(path: Path) -> None:
    """Report data is created for all examples."""
    assert path.is_file()
    _check_report(report_for_path(path))


def test_report_for_sbml_file() -> None:
    """A single SBML file is wrapped in an archive with one master model."""
    response = report_for_path(REPRESSILATOR_SBML)
    assert list(response.reports) == ["./model.xml"]
    assert response.reports["./model.xml"].report.models[0].id == "BIOMD0000000012"
    master = [e for e in response.manifest.entries if e.master]
    assert [(e.location, e.format) for e in master] == [
        ("./model.xml", "http://identifiers.org/combine.specifications/sbml")
    ]


def test_report_for_omex_has_all_sbml_entries() -> None:
    """Every SBML entry of an archive gets its own report."""
    response = report_for_path(OMEX_ICGMODEL)
    assert len(response.reports) == 3
    assert "./models/icg_body.xml" in response.reports


def test_report_for_sbml_string() -> None:
    """Report data is created from an SBML string."""
    entry = report_for_sbml(REPRESSILATOR_SBML.read_text(encoding="utf-8"))
    assert entry.report.models[0].id == "BIOMD0000000012"
    assert entry.debug.json_report_time.endswith(" [s]")


def test_report_json_is_camel_case() -> None:
    """The JSON of a response uses camelCase keys."""
    data = report_for_path(REPRESSILATOR_SBML).model_dump(mode="json", by_alias=True)
    report = data["reports"]["./model.xml"]["report"]
    assert set(report) == {
        "document",
        "models",
        "externalModelDefinitions",
        "linkGraph",
    }
    assert report["models"][0]["listOfSpecies"][0]["sbmlType"] == "Species"
    assert data["reports"]["./model.xml"]["debug"]["jsonReportTime"].endswith(" [s]")


def test_report_for_bytes_sbml() -> None:
    """Report data is created from the bytes of an SBML file."""
    _check_report(report_for_bytes(REPRESSILATOR_SBML.read_bytes()))


def test_report_for_bytes_omex() -> None:
    """Report data is created from the (binary) bytes of an archive."""
    response = report_for_bytes(OMEX_ICGMODEL.read_bytes())
    _check_report(response)
    assert len(response.reports) == 3


def test_report_for_bytes_gzipped_sbml() -> None:
    """Report data is created from gzipped SBML."""
    response = report_for_bytes(gzip.compress(REPRESSILATOR_SBML.read_bytes()))
    _check_report(response)
    assert list(response.reports) == ["./model.xml"]


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
    uid1 = report_for_path(REPRESSILATOR_SBML).uid
    uid2 = report_for_path(REPRESSILATOR_SBML).uid
    assert uid1 != uid2
