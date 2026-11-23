"""Tests of the report creation."""

import contextlib
import gzip
import logging
import os
import signal
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from collections.abc import Callable, Iterator
from functools import partial
from pathlib import Path

import libsbml
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from pymetadata.omex import Omex

from sbml4humans import isolation, limits, report, sbmlinfo
from sbml4humans.examples import ExampleMetaData, load_examples, report_for_example
from sbml4humans.limits import ContentTooLargeError
from sbml4humans.model import EdgeKind, ReportResponse, ResolutionStatus, SBase
from sbml4humans.report import (
    ReportInterruptedError,
    ReportJob,
    report_for_bytes,
    report_for_path,
    report_for_sbml,
    report_gzip_for_bytes,
)
from sbml4humans.resources import (
    BIOMODELS_CURATED_PATH,
    EXAMPLES_DIR,
    FBC_RECON3D_SBML,
    OMEX_COMPMODELS,
    OMEX_ICGMODEL,
    REPRESSILATOR_SBML,
)
from sbml4humans.sbmlinfo import MAX_UNIT_INFERENCE_DEPTH


# The report of a curated biomodel example is the one of its main SBML entry
# (`examples.py::report_for_example`), so `test_report_for_path` below never
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


@pytest.mark.parametrize(
    "example",
    [
        # the genome scale model takes minutes, see the `slow` marker in pyproject.toml
        pytest.param(e, marks=pytest.mark.slow)
        if e.file.name == "Recon3D.xml.gz"
        else e
        for e in load_examples().values()
    ],
    ids=lambda e: e.id,
)
def test_report_for_path(example: ExampleMetaData) -> None:
    """Report data, unique pks and a consistent link graph for every example."""
    assert example.file.is_file()
    _check_report(report_for_example(example))


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
    with Omex.from_omex(path) as archive:
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
        "odeSystem",
        "odeError",
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


@pytest.fixture
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The directory of the temporary files of the test, empty at its start."""
    root = tmp_path / "tmp"
    root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(root))
    return root


@pytest.mark.parametrize(
    "content",
    [
        REPRESSILATOR_SBML.read_bytes(),
        gzip.compress(REPRESSILATOR_SBML.read_bytes()),
        OMEX_ICGMODEL.read_bytes(),
        b"<not-sbml/>",
    ],
    ids=["sbml", "gzip", "omex", "invalid"],
)
def test_a_report_leaves_no_temporary_files(tmp_root: Path, content: bytes) -> None:
    """The content of a request does not stay on the server, also when it fails."""
    with contextlib.suppress(ValueError):
        report_for_bytes(content)
    assert list(tmp_root.iterdir()) == []


def test_a_report_of_a_path_leaves_no_temporary_files(tmp_root: Path) -> None:
    """Neither a file nor an archive nor the files next to a trusted file."""
    report_for_path(REPRESSILATOR_SBML)
    report_for_path(OMEX_COMPMODELS)
    report_for_path(EXAMPLES_DIR / "comp_deletion.xml", trusted=True)
    assert list(tmp_root.iterdir()) == []


def test_the_examples_leave_no_temporary_files(tmp_root: Path) -> None:
    """The examples, of which a biomodel is an entry of its archive."""
    load_examples.cache_clear()
    try:
        examples = load_examples()
        assert list(tmp_root.iterdir()) == []
        report_for_example(examples["BIOMD0000000001"])
        report_for_example(examples["icg_model"])
        assert list(tmp_root.iterdir()) == []
    finally:
        load_examples.cache_clear()


def test_a_gzip_bomb_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gzipped content is decompressed up to `MAX_CONTENT_SIZE`."""
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    with pytest.raises(ContentTooLargeError, match="1024 bytes"):
        report_for_bytes(gzip.compress(b" " * 4096))


def _archive(path: Path, entries: dict[str, bytes]) -> Path:
    """Write a COMBINE archive with a manifest and the entries."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.xml",
            '<omexManifest xmlns="http://identifiers.org/combine.specifications/'
            'omex-manifest"/>',
        )
        for name, content in entries.items():
            archive.writestr(name, content)
    return path


def test_an_archive_beyond_the_limits_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The number of entries, the size and the compression of an archive."""
    monkeypatch.setattr(limits, "MAX_ARCHIVE_ENTRIES", 3)
    many = _archive(tmp_path / "many.omex", {f"{k}.txt": b"x" for k in range(5)})
    with pytest.raises(ContentTooLargeError, match="more than 3 entries"):
        report_for_bytes(many.read_bytes())

    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    large = _archive(tmp_path / "large.omex", {"large.txt": b"x" * 2048})
    with pytest.raises(ContentTooLargeError, match="larger than the limit"):
        report_for_bytes(large.read_bytes())

    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 100 * 1024 * 1024)
    monkeypatch.setattr(limits, "COMPRESSION_RATIO_MIN_SIZE", 1024)
    bomb = _archive(tmp_path / "bomb.omex", {"bomb.txt": b"x" * 1024 * 1024})
    with pytest.raises(ContentTooLargeError, match="compressed more than"):
        report_for_bytes(bomb.read_bytes())


def test_a_trusted_path_is_not_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    """The limits protect the server from requests, not the user from own files."""
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    monkeypatch.setattr(limits, "MAX_ARCHIVE_ENTRIES", 1)
    _check_report(report_for_path(OMEX_ICGMODEL, trusted=True))


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


def test_out_of_memory_of_libsbml_is_a_memory_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A read which libsbml ends out of memory raises `MemoryError`, no read error.

    libsbml catches the failed allocation of the parser itself and logs the error
    `XMLOutOfMemory`; the child of a validation reports it as `memory` like a
    `MemoryError` of python.
    """
    from sbml4humans import report
    from sbml4humans.sbmlinfo import SBMLDocumentInfo

    def out_of_memory(source: Path | str) -> libsbml.SBMLDocument:
        doc = libsbml.SBMLDocument(3, 2)
        doc.getErrorLog().add(libsbml.SBMLError(libsbml.XMLOutOfMemory))
        return doc

    monkeypatch.setattr(SBMLDocumentInfo, "read", staticmethod(out_of_memory))
    with pytest.raises(MemoryError, match="Out of memory"):
        report._Entry(REPRESSILATOR_SBML)


# -------------------------------------------------------------------------------------
# a math the backend cannot typeset costs the latex of that math and nothing else
# -------------------------------------------------------------------------------------
def _level_1_kinetic_law_sbml(formula: str) -> bytes:
    """A Level 1 Version 2 document whose one kinetic law carries that formula.

    `KineticLaw::getMath` of a Level 1 document parses the attribute `formula`
    with the Level 1 parser, which is the one route into an AST the MathML
    writer of libsbml cannot write: it accepts `lambda()` and answers an
    `AST_LAMBDA` without children (issue #127).
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level1" level="1" version="2">'
        '<model name="crash"><listOfCompartments>'
        '<compartment name="c" volume="1"/></listOfCompartments><listOfSpecies>'
        '<species name="S1" compartment="c" initialAmount="1"/></listOfSpecies>'
        '<listOfReactions><reaction name="R1"><listOfReactants>'
        '<speciesReference species="S1" stoichiometry="1"/></listOfReactants>'
        f'<kineticLaw formula="{formula}"/></reaction></listOfReactions>'
        "</model></sbml>"
    ).encode()


@pytest.mark.parametrize("formula", ["lambda()", "1 + lambda()", "abs(lambda())"])
def test_a_lambda_without_children_keeps_the_report(formula: str) -> None:
    """A math which libsbml cannot write as MathML costs its latex alone.

    `writeMathMLToString` of libsbml segfaults on a childless lambda, whether
    it is the whole math or sits anywhere inside it (sbmlteam/libsbml#521), so
    the report of the document used to take the server process down with it.
    `formulaToL3String` writes the node as it was read, at any place.
    """
    response = report_for_bytes(_level_1_kinetic_law_sbml(formula))
    _check_report(response)
    (entry,) = response.reports.values()
    kinetic_law = entry.report.models[0].list_of_reactions[0].kinetic_law
    assert kinetic_law is not None
    assert kinetic_law.math is not None
    assert kinetic_law.math.formula == formula
    assert kinetic_law.math.latex is None


def _nested_difference_sbml(depth: int) -> bytes:
    """A document whose one assignment rule is `a - (a - (a - ...))`.

    The math is `depth` nested `apply` elements, the shape lxml refuses beyond
    a depth of 254 (issue #128). Every operand is the same parameter, so the
    model stays small whatever the depth is.
    """
    math = "<ci> a </ci>"
    for _ in range(depth):
        math = f"<apply><minus/><ci> a </ci>{math}</apply>"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" '
        'version="2"><model id="m"><listOfParameters>'
        '<parameter id="a" value="1" constant="true"/>'
        '<parameter id="x" constant="false"/></listOfParameters><listOfRules>'
        '<assignmentRule variable="x">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"{math}</math></assignmentRule></listOfRules></model></sbml>"
    ).encode()


@pytest.mark.parametrize(
    ("depth", "has_latex"), [(10, True), (255, False), (1000, False)]
)
def test_a_math_too_deep_for_lxml_keeps_the_report(depth: int, has_latex: bool) -> None:
    """A math too deep to convert costs its latex alone, not the whole report.

    lxml refuses a document deeper than 256 elements, which the MathML of 255
    nested applies is, and the report of the document used to fail with it. A
    math 1,000 levels deep is past the recursion limit of python as well, so
    the walks of `mathml.py` over the AST have to be iterative to answer it.
    """
    response = report_for_bytes(_nested_difference_sbml(depth))
    _check_report(response)
    (entry,) = response.reports.values()
    (rule,) = entry.report.models[0].list_of_rules
    assert rule.math is not None
    assert rule.math.formula.startswith("a - (a - (a")
    assert (rule.math.latex is not None) == has_latex


def _wide_sum_sbml(terms: int) -> bytes:
    """A document whose one assignment rule is the flat sum of `terms` names.

    The MathML reader of libsbml answers a right nested binary tree for a flat
    sum, so this math is `terms` levels deep: the shape of a real model which
    a recursive walk over the AST dies on, long before anything refuses the
    math itself.
    """
    parameters = "".join(
        f'<parameter id="x{k}" value="0" constant="false"/>' for k in range(terms)
    )
    cis = "".join(f"<ci> x{k} </ci>" for k in range(terms))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" '
        'version="1"><model id="m"><listOfParameters>'
        f'<parameter id="y" value="0" constant="false"/>{parameters}'
        '</listOfParameters><listOfRules><assignmentRule variable="y">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<apply><plus/>{cis}</apply></math></assignmentRule>"
        "</listOfRules></model></sbml>"
    ).encode()


@pytest.mark.parametrize("terms", [800, 1200])
def test_a_wide_sum_keeps_the_report_and_its_latex(terms: int) -> None:
    """A sum of a few hundred terms is typeset, and every symbol is linked.

    libsbml writes the nested tree of such a sum as the one flat `apply` it
    was read from, so the MathML is shallow and the latex is produced; the
    walks over the AST are what the depth of the tree used to break, at 499
    levels, which lost the whole report of the document.
    """
    response = report_for_bytes(_wide_sum_sbml(terms))
    _check_report(response)
    (entry,) = response.reports.values()
    (rule,) = entry.report.models[0].list_of_rules
    assert rule.math is not None
    assert rule.math.latex is not None
    symbols = {
        edge.target.split(":")[-1]
        for edge in entry.report.link_graph.edges
        if edge.source == rule.pk and edge.kind == EdgeKind.MATH
    }
    assert symbols == {f"x{k}" for k in range(terms)}


# -------------------------------------------------------------------------------------
# a math too deep for the unit inference of libsbml costs the derived units
# -------------------------------------------------------------------------------------
def _deep_constraint_sbml(depth: int) -> bytes:
    """A document whose one constraint compares a flat sum of that depth to zero.

    The MathML reader of libsbml answers a right nested binary tree for a flat
    sum, so the math of the constraint is `depth` levels deep: the comparison
    and the `depth - 1` terms below it. Its xml stays shallow, so the latex of
    the math is produced as it is for any other math, and the constraint is no
    part of the ODE system, so the whole report is there except for what the
    unit inference answers.
    """
    terms = "<ci> a </ci>" * (depth - 1)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" '
        'version="2"><model id="m" substanceUnits="mole" timeUnits="second" '
        'extentUnits="mole" volumeUnits="litre"><listOfParameters>'
        '<parameter id="a" value="1" constant="true" units="mole"/>'
        '<parameter id="x" value="0" constant="false" units="mole"/>'
        '</listOfParameters><listOfRules><assignmentRule variable="x">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        "<apply><times/><cn> 2 </cn><ci> a </ci></apply></math></assignmentRule>"
        "</listOfRules><listOfConstraints><constraint>"
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<apply><gt/><apply><plus/>{terms}</apply><cn> 0 </cn></apply>"
        "</math></constraint></listOfConstraints></model></sbml>"
    ).encode()


@pytest.mark.parametrize(
    ("depth", "derived"),
    [(MAX_UNIT_INFERENCE_DEPTH, "mol"), (MAX_UNIT_INFERENCE_DEPTH + 1, None)],
)
def test_a_math_too_deep_for_the_unit_inference_keeps_the_report(
    depth: int, derived: str | None
) -> None:
    """Past the bound the derived units are absent and nothing else changes.

    The unit inference of libsbml recurses over the math of the whole model on
    the first element of it which is asked for its derived units, and ends the
    process with SIGSEGV about 40,200 levels deep (issue #130), which no error
    response can answer. The report therefore does not ask for the derived
    units of a model which carries a math deeper than the bound, and the
    optional attribute stays absent for every element of it. At the bound they
    are reported, so the guard is no blanket switch of the inference.
    """
    response = report_for_bytes(_deep_constraint_sbml(depth))
    _check_report(response)
    (entry,) = response.reports.values()
    model = entry.report.models[0]
    assert [p.derived_units for p in model.list_of_parameters] == [derived, derived]
    (rule,) = model.list_of_rules
    assert rule.derived_units == derived
    # everything else of the report is there, whichever way the guard went
    assert [p.id for p in model.list_of_parameters] == ["a", "x"]
    assert rule.math is not None
    assert rule.math.latex is not None
    (constraint,) = model.list_of_constraints
    assert constraint.math is not None
    assert constraint.math.latex is not None
    assert entry.report.ode_error is None
    assert entry.report.ode_system is not None


# the report of a document in a child process, which a crash of libsbml ends
# with a signal instead of taking the test process down with it
_REPORT_IN_A_CHILD = """
import sys

from sbml4humans.report import report_for_bytes

with open(sys.argv[1], "rb") as f:
    response = report_for_bytes(f.read())
(entry,) = response.reports.values()
model = entry.report.models[0]
print(len(model.list_of_parameters), model.list_of_parameters[0].derived_units)
"""


def _report_in_a_child(tmp_path: Path, sbml: bytes) -> list[str]:
    """Build the report of a document in a child, answer what the child printed.

    The number of parameters of its model and the derived units of the first
    of them. A document which overflows the stack of libsbml ends the child
    with SIGSEGV rather than raising, so a report of one is tested in a child
    of its own: a regression ends that child and fails the test instead of
    taking the test process down with it.
    """
    assert len(sbml) < limits.MAX_CONTENT_SIZE
    source = tmp_path / "document.xml"
    source.write_bytes(sbml)
    child = subprocess.run(
        [sys.executable, "-c", _REPORT_IN_A_CHILD, str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert child.returncode == 0, (
        f"the report of the document ended the child with {child.returncode}: "
        f"{child.stderr[-2000:]}"
    )
    return child.stdout.split()


@pytest.mark.slow
def test_a_math_which_crashes_the_unit_inference_keeps_the_report(
    tmp_path: Path,
) -> None:
    """The report of the model of issue #130 is answered, in a child process.

    A model whose one assignment rule sums 45,000 parameters is 3 MB of xml,
    well inside `MAX_CONTENT_SIZE`, and libsbml reads it without a single
    error. Before the guard the first `getDerivedUnitDefinition()` of the
    report overflowed the stack of libsbml and the process died with SIGSEGV.
    """
    terms = 45000
    parameters = "".join(
        f'<parameter id="p{k}" value="1" constant="true" units="mole"/>'
        for k in range(terms)
    )
    cis = "".join(f"<ci> p{k} </ci>" for k in range(terms))
    sbml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" '
        'version="2"><model id="m"><listOfParameters>'
        f'{parameters}<parameter id="x" value="0" constant="false"/>'
        '</listOfParameters><listOfRules><assignmentRule variable="x">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<apply><plus/>{cis}</apply></math></assignmentRule>"
        "</listOfRules></model></sbml>"
    ).encode()
    assert _report_in_a_child(tmp_path, sbml) == [str(terms + 1), "None"]


# -------------------------------------------------------------------------------------
# a math which the unit inference expands past the bound, which is cheap to write
# -------------------------------------------------------------------------------------
def _function_model_sbml(definitions: str, rule_math: str) -> bytes:
    """A document with those function definitions and that assignment rule."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" '
        'version="2"><model id="m"><listOfParameters>'
        '<parameter id="a" value="1" constant="true" units="mole"/>'
        '<parameter id="x" value="0" constant="false" units="mole"/>'
        "</listOfParameters>"
        f"<listOfFunctionDefinitions>{definitions}</listOfFunctionDefinitions>"
        '<listOfRules><assignmentRule variable="x">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"{rule_math}</math></assignmentRule></listOfRules></model></sbml>"
    ).encode()


def _definition(sid: str, body: str) -> str:
    """One function definition of one bound variable `y` with that body."""
    return (
        f'<functionDefinition id="{sid}">'
        '<math xmlns="http://www.w3.org/1998/Math/MathML">'
        f"<lambda><bvar><ci> y </ci></bvar>{body}</lambda>"
        "</math></functionDefinition>"
    )


def _self_recursive_sbml() -> bytes:
    """`f0(y) = f0(y)`, the whole document under a kilobyte."""
    return _function_model_sbml(
        _definition("f0", "<apply><ci> f0 </ci><ci> y </ci></apply>"),
        "<apply><ci> f0 </ci><ci> a </ci></apply>",
    )


def _mutually_recursive_sbml() -> bytes:
    """`f0(y) = f1(y)` and `f1(y) = f0(y)`, a cycle of two."""
    definitions = "".join(
        _definition(f"f{k}", f"<apply><ci> f{1 - k} </ci><ci> y </ci></apply>")
        for k in (0, 1)
    )
    return _function_model_sbml(definitions, "<apply><ci> f0 </ci><ci> a </ci></apply>")


def _call_chain_sbml(links: int, nesting: int) -> bytes:
    """A chain of `links` definitions, the rule calling the first `nesting` deep.

    `f0` calls `f1`, `f1` calls `f2` and so on down to a definition which is
    its bound variable, and the rule is `f0(f0(...f0(a)...))`. The unit
    inference of libsbml follows every call into the body of its definition
    and walks the argument below it, so the recursion it costs is the length
    of the chain times the nesting of the calls, while the AST of the rule is
    `nesting + 1` levels deep.
    """
    definitions = "".join(
        _definition(
            f"f{k}",
            f"<apply><ci> f{k + 1} </ci><ci> y </ci></apply>"
            if k + 1 < links
            else "<ci> y </ci>",
        )
        for k in range(links)
    )
    math = "<ci> a </ci>"
    for _ in range(nesting):
        math = f"<apply><ci> f0 </ci>{math}</apply>"
    return _function_model_sbml(definitions, math)


@pytest.mark.parametrize(
    "document",
    [
        pytest.param(_self_recursive_sbml, id="a definition which calls itself"),
        pytest.param(_mutually_recursive_sbml, id="two definitions in a cycle"),
        pytest.param(
            partial(_call_chain_sbml, 200, 200), id="200 definitions called 200 deep"
        ),
    ],
)
def test_a_math_which_expands_too_deep_keeps_the_report(
    document: Callable[[], bytes], tmp_path: Path
) -> None:
    """A call of a function definition is what the unit inference descends into.

    It follows a `ci` which names a function definition into the body of that
    definition, once per call site and without remembering what it measured,
    so the depth of the AST as it stands says nothing about the recursion: a
    document of 714 bytes whose one definition calls itself, and one of 44 kB
    whose maths are 201 levels deep, both ended the process with SIGSEGV while
    every math of them is within the bound (issue #130). The guard therefore
    measures the expanded depth and refuses a cycle outright.
    """
    assert _report_in_a_child(tmp_path, document()) == ["2", "None"]


def test_a_model_which_calls_a_function_definition_reports_its_derived_units() -> None:
    """A function definition is no reason of its own to leave the units out.

    A chain of fifty definitions called twice is 101 expanded levels, far
    inside the bound, and the units of every element of the model are derived
    as they are without a function definition.
    """
    response = report_for_bytes(_call_chain_sbml(50, 2))
    _check_report(response)
    (entry,) = response.reports.values()
    model = entry.report.models[0]
    assert [p.derived_units for p in model.list_of_parameters] == ["mol", "mol"]
    (rule,) = model.list_of_rules
    assert rule.derived_units == "mol"
    assert len(model.list_of_function_definitions) == 50


# -------------------------------------------------------------------------------------
# the report of an untrusted source, which a child process builds
# -------------------------------------------------------------------------------------
def test_report_gzip_for_bytes_is_the_report_of_the_content() -> None:
    """The gzipped json of the child is the report of the content."""
    content = (EXAMPLES_DIR / "annotation.xml").read_bytes()
    packed = report_gzip_for_bytes(content)
    _check_report(ReportResponse.model_validate_json(gzip.decompress(packed)))


def test_the_report_of_untrusted_content_runs_in_a_child(
    spy_children: list[int],
) -> None:
    """Nothing of an untrusted source is read in the process of the server."""
    report_gzip_for_bytes((EXAMPLES_DIR / "annotation.xml").read_bytes())
    assert len(spy_children) == 1


def test_a_report_which_times_out_is_an_error(
    monkeypatch: pytest.MonkeyPatch, slow_content: bytes
) -> None:
    """A report beyond the timeout of its budget is an error the client reads."""
    monkeypatch.setattr(isolation, "MIN_CHILD_TIME", 0.1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "timeout", 1.0)
    with pytest.raises(ReportInterruptedError, match="longer than") as raised:
        report_gzip_for_bytes(slow_content)
    assert raised.value.interruption == "timeout"


@pytest.mark.skipif(sys.platform == "win32", reason="no resource limits on Windows")
def test_a_report_beyond_the_memory_of_a_child_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A report beyond the memory of its budget is an error, not an outage.

    The genome scale model needs far more than the lowered limit to be read,
    so the child either raises `MemoryError` or is aborted by the
    `std::bad_alloc` of libsbml, both of which the server answers.
    """
    monkeypatch.setattr(isolation.REPORT_BUDGET, "memory", 256 * 1024**2)
    with pytest.raises(ReportInterruptedError, match="more memory") as raised:
        report_gzip_for_bytes(FBC_RECON3D_SBML.read_bytes())
    assert raised.value.interruption == "memory"


@pytest.mark.parametrize(
    ("memory", "reads"),
    [
        (4 * 1024**3, "more memory than the 4 GiB a report may use"),
        (2 * 1024**3, "more memory than the 2 GiB a report may use"),
        (256 * 1024**2, "more memory than the 256 MiB a report may use"),
    ],
)
def test_the_memory_of_an_interruption_reads_in_its_unit(
    monkeypatch: pytest.MonkeyPatch, memory: int, reads: str
) -> None:
    """The bound of the memory reads in GiB, and below one GiB in MiB.

    The 4 GiB of the budget are the sentence the clients read; a bound a test
    lowered below one GiB would read as "the 0 GiB" in GiB.
    """
    monkeypatch.setattr(isolation.REPORT_BUDGET, "memory", memory)
    assert reads in str(ReportInterruptedError("memory"))


@pytest.mark.parametrize("interruption", ["timeout", "memory", "crashed", "busy"])
def test_the_sentences_of_an_interruption_name_their_work(
    interruption: isolation.Interruption,
) -> None:
    """Every sentence names the work its client asked for and never the other.

    A client which asked for the ODE system of a document reads of that file,
    not of a report it never asked for, and the other way around.
    """
    of_report = str(ReportInterruptedError(interruption, "report"))
    of_ode = str(ReportInterruptedError(interruption, "ode system"))
    assert "ODE" not in of_report
    assert "report" not in of_ode
    assert of_report != of_ode
    # a report is the work of an error which names none
    assert str(ReportInterruptedError(interruption)) == of_report


def test_a_report_which_fails_logs_its_time(caplog: pytest.LogCaptureFixture) -> None:
    """The time of a report is logged also when it raised, which a reader wants most."""
    content = b'<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core"/>'
    with (
        caplog.at_level(logging.INFO, logger="sbml4humans.report"),
        pytest.raises(ValueError, match="No SBML model"),
    ):
        report_gzip_for_bytes(content)
    assert f"report of {len(content)} bytes in " in caplog.text


def _killed_after_first_send(job: ReportJob) -> Iterator[tuple[str, bytes]]:
    """Send one result, then end the child by the signal of the OOM killer."""
    yield report._REPORT, b""
    os.kill(os.getpid(), signal.SIGKILL)


@pytest.mark.skipif(sys.platform == "win32", reason="no signals on Windows")
def test_a_child_killed_while_it_sends_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A report of which the server got only a part is no report at all."""
    monkeypatch.setattr(report, "report_gzip", _killed_after_first_send)
    with pytest.raises(
        ReportInterruptedError, match="The document could not be reported"
    ) as raised:
        report_gzip_for_bytes(b"<sbml/>")
    assert raised.value.interruption == "crashed"
    assert raised.value.work == "report"


def test_a_report_which_got_no_child_is_an_error(
    monkeypatch: pytest.MonkeyPatch, spy_children: list[int]
) -> None:
    """A server busy with other reports says so instead of waiting on."""
    monkeypatch.setattr(isolation.REPORT_BUDGET, "concurrency", 1)
    monkeypatch.setattr(isolation.REPORT_BUDGET, "timeout", 1.0)
    # another request holds the one child
    semaphore = isolation._semaphore(isolation.REPORT_BUDGET)
    semaphore.acquire()
    try:
        with pytest.raises(
            ReportInterruptedError, match="busy with other reports"
        ) as raised:
            report_gzip_for_bytes((EXAMPLES_DIR / "annotation.xml").read_bytes())
    finally:
        semaphore.release()
    assert raised.value.interruption == "busy"
    assert spy_children == []


def test_a_document_without_a_model_is_an_error_through_the_child() -> None:
    """The error of the child is raised in the server, with its traceback."""
    content = b'<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core"/>'
    with pytest.raises(ValueError, match="No SBML model") as raised:
        report_gzip_for_bytes(content)
    assert any("child process" in note for note in raised.value.__notes__)


def test_the_limits_of_the_server_reach_the_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A child reads the source within the limits of its server, which it is given.

    A child of the forkserver does not see a `monkeypatch` of the server, so
    the limits go to it in its job.
    """
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    with pytest.raises(ContentTooLargeError, match="1024 bytes"):
        report_gzip_for_bytes(gzip.compress(b" " * 4096))


def test_a_trusted_path_is_reported_in_this_process(spy_children: list[int]) -> None:
    """The examples and the files of the user are read without a child."""
    _check_report(report_for_path(EXAMPLES_DIR / "annotation.xml", trusted=True))
    assert spy_children == []


# -------------------------------------------------------------------------------------
# the proof of the isolation: a crash of libsbml is an answer, not an outage
# -------------------------------------------------------------------------------------
def _derives_units_unguarded(
    self: sbmlinfo.SBMLDocumentInfo, model: libsbml.Model
) -> bool:
    """Ask libsbml for the derived units of every model, whatever its math is."""
    return True


def _report_gzip_unguarded(job: ReportJob) -> Iterator[tuple[str, bytes]]:
    """Report a source in the child, with the guard of the unit inference lifted.

    `SBMLDocumentInfo._derives_units` is the whole guard: it answers false for
    a model one math of which costs more than `MAX_UNIT_INFERENCE_DEPTH` levels
    of recursion, every call of a function definition expanded, and for one
    whose function definitions hold a cycle. A guard which answers true is the
    report as it was before the guard, which is what the isolation has to
    survive.

    It is lifted here and not in the server, because a child is forked from a
    forkserver which imported `sbmlinfo` before any `monkeypatch` of the
    server, so a patched attribute of the server never reaches the child and
    the guard would hold inside it. `multiprocessing` pickles the function of a
    child by its name, so the child imports this module and runs this
    replacement of `report.report_gzip`, which lifts the guard where libsbml
    runs.

    Args:
        job: the source and the limits it is read within.

    Yields:
        The one pair of `report.report_gzip`, for a document which survives.
    """
    sbmlinfo.SBMLDocumentInfo._derives_units = _derives_units_unguarded
    yield from report.report_gzip(job)


@pytest.mark.skipif(sys.platform == "win32", reason="no signals on Windows")
@pytest.mark.parametrize(
    "document",
    [
        pytest.param(_self_recursive_sbml, id="a definition which calls itself"),
        pytest.param(_mutually_recursive_sbml, id="two definitions in a cycle"),
        pytest.param(
            partial(_call_chain_sbml, 200, 200), id="200 definitions called 200 deep"
        ),
        # 3 MB of xml and no test of minutes: the child dies on the first
        # element of the model it builds, so this shape costs the read of the
        # document and the crash alone, as the three cheap ones above do
        pytest.param(partial(_wide_sum_sbml, 45000), id="a sum of 45,000 terms"),
    ],
)
def test_a_document_which_crashes_libsbml_is_an_error_and_the_server_lives(
    document: Callable[[], bytes],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A document which ends the process of libsbml costs its one request.

    Three times a document which libsbml read without a single error ended the
    process which built its report (issues #127 and #130), and every guard
    which keeps one of those shapes out of libsbml is narrow by construction:
    it holds the shape which was measured and says nothing of the next one.
    With the guard of the unit inference lifted inside the child, each of the
    shapes of #130 crashes libsbml again, and the client reads the one sentence
    of an interrupted report while the process which answered it reports the
    next document. Without the child the crash ends the process which asked for
    the report, this test process, with SIGSEGV, which no response can answer.
    """
    monkeypatch.setattr(report, "report_gzip", _report_gzip_unguarded)
    with pytest.raises(ReportInterruptedError, match="ended unexpectedly") as raised:
        report_gzip_for_bytes(document())
    assert raised.value.interruption == "crashed"
    assert raised.value.work == "report"
    # the segmentation fault of libsbml is what ended the child, not an error of
    # python and not a child which never ran
    assert f"exit code -{signal.SIGSEGV}" in caplog.text
    # this process lived: the next document is reported as every other one is,
    # by a child of the report as the server gives it
    monkeypatch.undo()
    packed = report_gzip_for_bytes((EXAMPLES_DIR / "annotation.xml").read_bytes())
    _check_report(ReportResponse.model_validate_json(gzip.decompress(packed)))


@pytest.mark.skipif(sys.platform == "win32", reason="no signals on Windows")
def test_a_crash_of_libsbml_is_an_error_of_the_contract(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A client of the api reads a crash of libsbml as the error of its request.

    The one sentence of the interruption, status 200 like every answer of the
    contract, no warning and no traceback for a request which sets no
    `api.TRACEBACK_STATE`, and the next request is answered with its report.
    """
    monkeypatch.setattr(report, "report_gzip", _report_gzip_unguarded)
    response = client.post("/api/content", content=_self_recursive_sbml())
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"errors", "warnings", "info"}
    assert data["errors"] == [
        "The document could not be reported: the process which read it ended "
        "unexpectedly."
    ]
    assert data["warnings"] == []
    assert data["info"] == {}
    # the server lived: it answers the next request with the report of its document
    monkeypatch.undo()
    answer = client.post("/api/content", content=REPRESSILATOR_SBML.read_bytes())
    assert answer.status_code == 200
    _check_report(ReportResponse.model_validate(answer.json()))
