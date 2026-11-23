"""Tests of the report creation."""

import contextlib
import gzip
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

import libsbml
import pytest
from pydantic import BaseModel
from pymetadata.omex import Omex

from sbml4humans import limits
from sbml4humans.examples import ExampleMetaData, load_examples, report_for_example
from sbml4humans.limits import ContentTooLargeError
from sbml4humans.model import EdgeKind, ReportResponse, ResolutionStatus, SBase
from sbml4humans.report import report_for_bytes, report_for_path, report_for_sbml
from sbml4humans.resources import (
    BIOMODELS_CURATED_PATH,
    EXAMPLES_DIR,
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


@pytest.mark.slow
def test_a_math_which_crashes_the_unit_inference_keeps_the_report(
    tmp_path: Path,
) -> None:
    """The report of the model of issue #130 is answered, in a child process.

    A model whose one assignment rule sums 45,000 parameters is 3 MB of xml,
    well inside `MAX_CONTENT_SIZE`, and libsbml reads it without a single
    error. Before the guard the first `getDerivedUnitDefinition()` of the
    report overflowed the stack of libsbml and the process died with SIGSEGV,
    which is why the report runs in a child here: a regression ends that child
    with the signal rather than the test process.
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
    source = tmp_path / "wide.xml"
    source.write_bytes(sbml)
    assert len(sbml) < limits.MAX_CONTENT_SIZE

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
    assert child.stdout.split() == [str(terms + 1), "None"]
