"""Tests of the report creation."""

import gzip
import tempfile
from collections import Counter
from pathlib import Path

import pytest
from pydantic import BaseModel
from pymetadata.omex import Omex

from sbml4humans.examples import ExampleMetaData, load_examples
from sbml4humans.model import ReportResponse, SBase
from sbml4humans.report import report_for_bytes, report_for_path, report_for_sbml
from sbml4humans.resources import (
    BIOMODELS_CURATED_PATH,
    OMEX_ICGMODEL,
    REPRESSILATOR_SBML,
)


# `ExampleMetaData.file` of a curated biomodel is its extracted main SBML file
# (`examples.py::biomodel_examples`), so `test_report_for_path` below never
# exercises `Omex.from_omex` on these archives' real, multi-file manifests.
# Kept to ten archives so the suite stays fast.
BIOMODEL_ARCHIVES = sorted(BIOMODELS_CURATED_PATH.glob("BIOMD*.omex"))[:10]


def _collect_pks(obj: object) -> list[str]:
    """The pk of every `SBase` nested anywhere in a pydantic report object."""
    pks: list[str] = []
    if isinstance(obj, SBase):
        pks.append(obj.pk)
    if isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            pks.extend(_collect_pks(getattr(obj, name)))
    elif isinstance(obj, dict):
        for item in obj.values():
            pks.extend(_collect_pks(item))
    elif isinstance(obj, list | tuple):
        for item in obj:
            pks.extend(_collect_pks(item))
    return pks


def _check_report(response: ReportResponse) -> None:
    """Check the report response: its structure, unique pks and link graph.

    No two elements of a report, nor two link graph nodes, share a pk, and
    the nodes of the link graph are exactly the elements of the report.
    """
    assert len(response.uid) == 32
    assert response.manifest.entries
    assert all(e.location and e.format for e in response.manifest.entries)
    assert len([e for e in response.manifest.entries if e.master]) <= 1
    assert response.reports
    for location, entry in response.reports.items():
        assert location.startswith("./")
        assert entry.report.document.level in {1, 2, 3}
        assert entry.debug.json_report_time.endswith(" [s]")
        pks = _collect_pks(entry.report)
        duplicates = {pk for pk, count in Counter(pks).items() if count > 1}
        assert not duplicates, f"{location}: duplicate pks {duplicates}"
        nodes = entry.report.link_graph.nodes
        assert all(key == node.pk for key, node in nodes.items())
        element_pks = set(pks)
        node_pks = set(nodes)
        assert node_pks == element_pks, (
            f"{location}: node pks and element pks differ by {node_pks ^ element_pks}"
        )


@pytest.mark.parametrize("example", list(load_examples().values()), ids=lambda e: e.id)
def test_report_for_path(example: ExampleMetaData) -> None:
    """Report data, unique pks and a consistent link graph for every example."""
    assert example.file.is_file()
    _check_report(report_for_path(example.file))


@pytest.mark.parametrize("path", BIOMODEL_ARCHIVES, ids=lambda p: p.name)
def test_report_for_biomodel_archive(path: Path) -> None:
    """Report data for a curated BioModels archive read directly.

    Reading the archive itself, rather than its extracted main SBML file,
    exercises `Omex.from_omex` on a real multi-file manifest (the omex entry,
    `manifest.xml`, the SBML model, possibly more).
    """
    response = report_for_path(path)
    _check_report(response)
    assert any(e.location.endswith(".xml") for e in response.manifest.entries)
    archive = Omex.from_omex(path)
    if any(e.master for e in archive.manifest.entries):
        assert any(e.master for e in response.manifest.entries)


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


def test_error_of_unreadable_content_names_no_path() -> None:
    """The error of content which is not SBML holds the libsbml diagnosis alone.

    The user reads this message. The temporary file the content was written to
    is the business of the server and is only logged, not shown.
    """
    with pytest.raises(ValueError) as error:
        report_for_bytes(b"<not-sbml/>")
    message = str(error.value)
    assert message.startswith("No SBML model could be read:")
    assert "line 1:" in message
    assert tempfile.gettempdir() not in message
    assert "model.xml" not in message


def test_uid_differs_between_reports() -> None:
    """Every report gets its own uid."""
    uid1 = report_for_path(REPRESSILATOR_SBML).uid
    uid2 = report_for_path(REPRESSILATOR_SBML).uid
    assert uid1 != uid2
