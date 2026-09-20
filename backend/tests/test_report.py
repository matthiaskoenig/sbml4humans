"""Tests of the report creation."""

import gzip
import tempfile
from collections import Counter
from pathlib import Path

import pytest
from pydantic import BaseModel
from pymetadata.omex import Omex

from sbml4humans.examples import ExampleMetaData, load_examples
from sbml4humans.model import ReportResponse, ResolutionStatus, SBase
from sbml4humans.report import report_for_bytes, report_for_path, report_for_sbml
from sbml4humans.resources import (
    BIOMODELS_CURATED_PATH,
    EXAMPLES_DIR,
    OMEX_COMPMODELS,
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

    No two elements of a report, nor two link graph nodes, share a pk, the
    nodes of the link graph are exactly the elements of the report, and no
    edge is repeated: two attributes of one element which name the same
    element, the substance and the extent units of a model, are one link.
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
        edges = entry.report.link_graph.edges
        repeated = {edge for edge, count in Counter(edges).items() if count > 1}
        assert not repeated, f"{location}: repeated edges {repeated}"


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


def test_report_for_omex_keeps_the_order_of_the_manifest() -> None:
    """The manifest and the reports of a response are in the order of the manifest.

    The order of the file system must not show, which pymetadata 0.6.4 ensures.
    """
    response = report_for_path(OMEX_ICGMODEL)
    locations = [
        "./models/icg_liver.xml",
        "./models/icg_body.xml",
        "./models/icg_body_flat.xml",
    ]
    assert [entry.location for entry in response.manifest.entries] == [
        ".",
        "./manifest.xml",
        *locations,
    ]
    assert list(response.reports) == locations


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


# -------------------------------------------------------------------------------------
# external model definitions: the entries of an archive, the files of a trusted directory
# -------------------------------------------------------------------------------------
def _across(response: ReportResponse, location: str) -> set[tuple[str, str]]:
    """The entry and the target of every edge of an entry which leaves it."""
    graph = response.reports[location].report.link_graph
    return {
        (edge.target_entry, edge.target)
        for edge in graph.edges
        if edge.target_entry is not None
    }


def test_an_archive_is_linked_across_its_entries() -> None:
    """The replaced elements of `omex_comp.xml` end in `omex_minimal.xml`."""
    response = report_for_path(OMEX_COMPMODELS)
    comp = response.reports["./models/omex_comp.xml"].report
    for emd in comp.external_model_definitions:
        assert emd.resolution.status == ResolutionStatus.RESOLVED
        assert emd.resolution.entry == "./models/omex_minimal.xml"
        assert emd.resolution.model == "omex_minimal/Model:omex_minimal"
        assert emd.resolution.md5_matches is None
    across = _across(response, "./models/omex_comp.xml")
    assert ("./models/omex_minimal.xml", "omex_minimal/Species:S1") in across
    assert {entry for entry, _ in across} == {"./models/omex_minimal.xml"}
    # every target is a node of the graph of its entry
    nodes = response.reports["./models/omex_minimal.xml"].report.link_graph.nodes
    assert {target for _, target in across} <= set(nodes)


def test_a_trusted_file_reads_the_files_next_to_it() -> None:
    """The documents a single file names become further entries of its archive."""
    response = report_for_path(EXAMPLES_DIR / "comp_deletion.xml", trusted=True)
    assert [(e.location, e.master) for e in response.manifest.entries if e.master] == [
        ("./comp_deletion.xml", True)
    ]
    assert list(response.reports) == ["./comp_deletion.xml", "./unit_definitions.xml"]
    emd = response.reports["./comp_deletion.xml"].report.external_model_definitions[0]
    assert emd.resolution.status == ResolutionStatus.RESOLVED
    assert emd.resolution.entry == "./unit_definitions.xml"
    # the md5 of the file is the one the definition states
    assert emd.resolution.md5_matches is True
    assert _across(response, "./comp_deletion.xml") == {
        ("./unit_definitions.xml", "unit_definitions/Model:unit_definitions"),
        ("./unit_definitions.xml", "unit_definitions/UnitDefinition:mg_per_day"),
    }


def test_an_untrusted_file_reads_nothing_else() -> None:
    """An upload has no directory, whatever lies next to its temporary file."""
    for response in (
        report_for_path(EXAMPLES_DIR / "comp_deletion.xml"),
        report_for_bytes((EXAMPLES_DIR / "comp_deletion.xml").read_bytes()),
    ):
        assert list(response.reports) == ["./model.xml"]
        emd = response.reports["./model.xml"].report.external_model_definitions[0]
        assert emd.resolution.status == ResolutionStatus.NOT_FOUND
        assert _across(response, "./model.xml") == set()


def _body(source: str) -> str:
    """A comp document whose external model definition names the source."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1"
      level="3" version="1" comp:required="true">
  <model id="body"/>
  <comp:listOfExternalModelDefinitions>
    <comp:externalModelDefinition comp:id="emd" comp:source="{source}"/>
  </comp:listOfExternalModelDefinitions>
</sbml>
"""


def test_trusted_files_are_read_transitively(tmp_path: Path) -> None:
    """A file which is read names files of its own, relative to where it is."""
    (tmp_path / "body.xml").write_text(_body("organs/liver.xml"))
    (tmp_path / "organs").mkdir()
    (tmp_path / "organs" / "liver.xml").write_text(_body("../cell.xml"))
    (tmp_path / "cell.xml").write_text(_body("https://example.org/remote.xml"))
    response = report_for_path(tmp_path / "body.xml", trusted=True)
    assert list(response.reports) == ["./body.xml", "./organs/liver.xml", "./cell.xml"]
    statuses = {
        location: entry.report.external_model_definitions[0].resolution.status
        for location, entry in response.reports.items()
    }
    assert statuses == {
        "./body.xml": ResolutionStatus.RESOLVED,
        "./organs/liver.xml": ResolutionStatus.RESOLVED,
        "./cell.xml": ResolutionStatus.REMOTE_SOURCE,
    }


@pytest.mark.parametrize("source", ["../secret.xml", "{absolute}", "missing.xml"])
def test_nothing_outside_of_the_trusted_directory_is_read(
    tmp_path: Path, source: str
) -> None:
    """Neither a file above the directory, nor an absolute path, nor a missing one."""
    secret = tmp_path / "secret.xml"
    secret.write_text(_body("unused.xml"))
    directory = tmp_path / "models"
    directory.mkdir()
    (directory / "body.xml").write_text(_body(source.format(absolute=secret)))
    response = report_for_path(directory / "body.xml", trusted=True)
    assert list(response.reports) == ["./body.xml"]
    emd = response.reports["./body.xml"].report.external_model_definitions[0]
    assert emd.resolution.status == ResolutionStatus.NOT_FOUND


def test_a_link_out_of_the_trusted_directory_is_not_followed(tmp_path: Path) -> None:
    """A symbolic link does not make a file outside of the directory a part of it."""
    secret = tmp_path / "secret.xml"
    secret.write_text(_body("unused.xml"))
    directory = tmp_path / "models"
    directory.mkdir()
    (directory / "liver.xml").symlink_to(secret)
    (directory / "body.xml").write_text(_body("liver.xml"))
    response = report_for_path(directory / "body.xml", trusted=True)
    assert list(response.reports) == ["./body.xml"]
