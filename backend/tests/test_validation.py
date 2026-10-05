"""Tests of the validation of a document and the mapping of its issues."""

import http.server
import os
import signal
import threading
import time
import zipfile
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

import libsbml
import pytest

from sbml4humans import isolation, report, validation
from sbml4humans.model import EntryValidation, ValidationResponse
from sbml4humans.report import (
    report_for_bytes,
    report_for_path,
    validation_for_bytes,
    validation_for_path,
)
from sbml4humans.resources import EXAMPLES_DIR
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.validation import (
    _RESOLVER,
    MAX_EXPANDED_ELEMENTS,
    ElementPositions,
    ReportDocuments,
    ReportResolver,
    expanded_size,
    issues_of,
    validate,
    validate_entries,
)


COMP_DELETION = EXAMPLES_DIR / "comp_deletion.xml"


def _issues(source: str) -> list[tuple[int, str, str]]:
    """The rule, severity and pk of every issue of a document after the check."""
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(source))
    info.build_report()
    info.doc.checkConsistency()
    return [(i.rule, i.severity, i.pk) for i in issues_of(info.doc, info.positions)]


def _report_pks(info: SBMLDocumentInfo) -> list[str]:
    """The pk of every element of the report of a document."""
    pks: list[str] = []

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            if "pk" in obj and "sbmlType" in obj:
                pks.append(obj["pk"])
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(info.report.model_dump(by_alias=True))
    return pks


def test_example_issues_on_their_elements() -> None:
    """Every issue of the example goes to the element it concerns."""
    issues = _issues(str(EXAMPLES_DIR / "validation.xml"))
    by_rule: dict[int, set[str]] = {}
    for rule, _, pk in issues:
        by_rule.setdefault(rule, set()).add(pk)
    assert by_rule[10601] == {"validation/Model:validation"}
    assert by_rule[10712] == {"validation/Compartment:cell"}
    assert by_rule[10703] == by_rule[20702] == {"validation/Parameter:k1"}
    assert by_rule[99505] == {
        "validation/AssignmentRule:x",
        "validation/KineticLaw:R1.kineticLaw",
    }
    severities = {rule: severity for rule, severity, _ in issues}
    assert severities[10601] == "error"
    assert severities[10712] == "warning"


def test_valid_example_has_no_issues() -> None:
    """A valid document has no issues."""
    assert _issues(str(EXAMPLES_DIR / "species.xml")) == []


def test_read_errors_are_kept() -> None:
    """A read error stays in the log after the check and comes first."""
    sbml = (EXAMPLES_DIR / "minimal_model.xml").read_text()
    issues = _issues(sbml.replace("<model ", '<model foo="1" ', 1))
    assert issues[0][0] == 20222
    assert issues[0][1] == "error"
    assert issues[0][2] == "minimal_model/Model:minimal_model"


def test_duplicates_are_dropped() -> None:
    """An issue libsbml logs twice is one issue."""
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(str(EXAMPLES_DIR / "validation.xml")))
    info.build_report()
    info.doc.checkConsistency()
    log: libsbml.SBMLErrorLog = info.doc.getErrorLog()
    log.add(info.doc.getError(0))
    issues = issues_of(info.doc, info.positions)
    keys = [(i.rule, i.line, i.column, i.message) for i in issues]
    assert len(keys) == len(set(keys))


def test_one_line_document() -> None:
    """Elements on one line are told apart by their column, every issue has a pk."""
    sbml = " ".join((EXAMPLES_DIR / "validation.xml").read_text().split())
    issues = _issues(sbml)
    assert issues
    pks = {rule: pk for rule, _, pk in issues}
    assert pks[10712] == "validation/Compartment:cell"
    assert pks[10703] == "validation/Parameter:k1"


def test_position_before_every_element_is_the_document() -> None:
    """A position before the first element, or line 0, is the document."""
    positions = ElementPositions("document/SBMLDocument:document")
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(
        str(EXAMPLES_DIR / "species.xml")
    )
    model: libsbml.Model = doc.getModel()
    positions.add(model, "species/Model:species")
    assert positions.pk_at(0, 0) == "document/SBMLDocument:document"
    assert positions.pk_at(1, 1) == "document/SBMLDocument:document"
    assert positions.pk_at(model.getLine() + 1, 1) == "species/Model:species"


@pytest.mark.parametrize("name", ["model_composition.xml", "minimal_model_comp.xml"])
def test_comp_examples_map_every_issue(name: str) -> None:
    """Every issue of a comp example has a pk of the report."""
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(str(EXAMPLES_DIR / name)))
    info.build_report()
    info.doc.checkConsistency()
    issues = issues_of(info.doc, info.positions)
    assert issues
    assert {i.pk for i in issues} <= set(_report_pks(info))


def test_unit_warnings_of_the_reaction_example() -> None:
    """The units of the compartment and of the species of the example are missing."""
    entry = _entry(validation_for_path(EXAMPLES_DIR / "reaction.xml"))
    units = {
        (issue.rule, issue.severity, issue.pk)
        for issue in entry.issues
        if issue.rule in {20513, 20616}
    }
    assert units == {
        (20513, "warning", "reaction/Compartment:c"),
        (20616, "warning", "reaction/Species:x"),
        (20616, "warning", "reaction/Species:y"),
    }


def test_unresolved_comp_example_marks_its_submodels_and_definitions() -> None:
    """Without the file they name, the definitions and the submodels are errors."""
    content = (EXAMPLES_DIR / "minimal_model_comp.xml").read_bytes()
    entry = _entry(validation_for_bytes(content))
    comp = {
        (issue.rule, issue.severity, issue.pk)
        for issue in entry.issues
        if issue.rule in {1020615, 1090101}
    }
    assert comp == {
        *(
            (1020615, "error", f"minimal_model_comp/Submodel:submodel{k}")
            for k in range(5)
        ),
        *(
            (1090101, "error", f"document/ExternalModelDefinition:emd{k}")
            for k in range(5)
        ),
    }


def test_issue_on_a_list_without_content_goes_to_its_owner() -> None:
    """An issue on a list the report does not carry is the issue of the owner."""
    sbml = (EXAMPLES_DIR / "validation.xml").read_text()
    sbml = sbml.replace("<listOfParameters>", '<listOfParameters foo="1">')
    issues = _issues(sbml)
    assert (20227, "error", "validation/Model:validation") in issues


def test_issue_on_a_list_of_a_reaction_goes_to_the_reaction() -> None:
    """The lists of a reaction and of its kinetic law belong to their owner."""
    sbml = (EXAMPLES_DIR / "validation.xml").read_text()
    sbml = sbml.replace("<listOfReactants>", '<listOfReactants foo="1">')
    issues = _issues(sbml)
    assert (21150, "error", "validation/Reaction:R1") in issues


def _entry(
    response: ValidationResponse, location: str | None = None
) -> EntryValidation:
    """An entry of a validation response, the first by default."""
    entries = response.entries
    return entries[location] if location else next(iter(entries.values()))


def _rules(response: ValidationResponse, location: str | None = None) -> set[int]:
    """The rules of the issues of an entry of a response, the first by default."""
    return {issue.rule for issue in _entry(response, location).issues}


def test_untrusted_source_is_not_read() -> None:
    """An absolute path or a url of an untrusted document is never resolved."""
    requests: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        """A server which records every request."""

        def do_GET(self) -> None:
            """Record the request and answer that nothing is there."""
            requests.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            """Log nothing."""

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        target = (EXAMPLES_DIR / "unit_definitions.xml").resolve()
        sbml = COMP_DELETION.read_text()
        for source in (str(target), f"http://127.0.0.1:{server.server_port}/u.xml"):
            content = sbml.replace(
                'comp:source="unit_definitions.xml"', f'comp:source="{source}"'
            )
            response = validation_for_bytes(content.encode())
            assert 1090101 in _rules(response), source
        assert requests == []
    finally:
        server.shutdown()


def test_untrusted_absolute_source_opens_no_file() -> None:
    """The resolver answers no absolute path, whatever libsbml asks."""
    target = (EXAMPLES_DIR / "unit_definitions.xml").resolve()
    sbml = COMP_DELETION.read_text().replace(
        'comp:source="unit_definitions.xml"', f'comp:source="{target}"'
    )
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromString(sbml)
    issues = validate(doc, ElementPositions("d"))
    assert 1090101 in {i.rule for i in issues}


def test_neighbour_file_is_not_read_by_the_validation() -> None:
    """A file next to the document is not resolved unless the report gives it."""
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(COMP_DELETION))
    issues = validate(doc, ElementPositions("d"))
    assert 1090101 in {i.rule for i in issues}


def _spy_find(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str | None, str]]:
    """Record every request of the resolver: source, base and the found model.

    The resolver answers in the child process of the validation, where a spy of
    the test sees nothing, so the entries are validated in this process.
    """
    found: list[tuple[str, str | None, str]] = []
    find = ReportDocuments.find

    def spy(
        self: ReportDocuments, source: str, base: str | None
    ) -> libsbml.SBMLDocument | None:
        doc = find(self, source, base)
        found.append((source, base, doc.getModel().getId() if doc else ""))
        return doc

    monkeypatch.setattr(ReportDocuments, "find", spy)
    _in_process(monkeypatch)
    return found


def _in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate in this process rather than in a child process."""

    def run_here(
        function: Callable[[Any], Iterable[tuple[str, Any]]],
        argument: Any,
        keys: list[str],
    ) -> dict[str, Any]:
        """The results of the function, without a child process."""
        return dict(function(argument))

    monkeypatch.setattr(isolation, "run_isolated", run_here)


@pytest.mark.parametrize("child", [False, True])
def test_trusted_neighbour_is_resolved_from_the_report(
    monkeypatch: pytest.MonkeyPatch, child: bool
) -> None:
    """A source the report read is resolved for the validation, without 1090101."""
    found = [] if child else _spy_find(monkeypatch)
    response = validation_for_path(COMP_DELETION, trusted=True)
    assert "./unit_definitions.xml" in response.entries
    if not child:
        assert (
            "unit_definitions.xml",
            "./comp_deletion.xml",
            "unit_definitions",
        ) in found
    assert 1090101 not in _rules(response, "./comp_deletion.xml")


_COMP = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" '
    'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
    'level="3" version="1" comp:required="true">{}</sbml>'
)


def _emds(*emds: tuple[str, str, str]) -> str:
    """A list of external model definitions of id, source and model."""
    return (
        "<comp:listOfExternalModelDefinitions>"
        + "".join(
            f'<comp:externalModelDefinition comp:id="{i}" comp:source="{source}" '
            f'comp:modelRef="{ref}"/>'
            for i, source, ref in emds
        )
        + "</comp:listOfExternalModelDefinitions>"
    )


# m.xml names Bx of sub/b.xml, which is an external model definition of
# sub/b.xml naming c.xml, relative to sub/; ./c.xml is another document
_CHAIN = {
    "m.xml": _COMP.format(
        '<model id="M"><comp:listOfSubmodels>'
        '<comp:submodel comp:id="s" comp:modelRef="Bx"/>'
        '<comp:submodel comp:id="w" comp:modelRef="Wx"/>'
        "</comp:listOfSubmodels></model>"
        + _emds(("Bx", "sub/b.xml", "Bx"), ("Wx", "c.xml", "W"))
    ),
    "sub/b.xml": _COMP.format('<model id="B"/>' + _emds(("Bx", "c.xml", "C"))),
    "sub/c.xml": _COMP.format('<model id="C"/>'),
    "c.xml": _COMP.format('<model id="W"/>'),
}
_UNRESOLVED = {1090101, 1090104, 1020615}


def _check_chain(
    response: ValidationResponse, found: list[tuple[str, str | None, str]] | None
) -> None:
    """The chain is resolved within the report, each source against its base."""
    assert {"./m.xml", "./sub/b.xml", "./sub/c.xml", "./c.xml"} <= set(response.entries)
    for location, entry in response.entries.items():
        assert entry.skipped is None, location
        rules = {issue.rule for issue in entry.issues}
        assert not rules & _UNRESOLVED, location
    if found is None:
        return
    assert ("c.xml", "sub/b.xml", "C") in found
    assert ("c.xml", "./m.xml", "W") in found
    assert {model for source, _, model in found if source == "c.xml"} == {"C", "W"}


@pytest.mark.parametrize("child", [False, True])
def test_chained_sources_resolve_against_their_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, child: bool
) -> None:
    """A chain of external model definitions of trusted files is followed."""
    for name, content in _CHAIN.items():
        (tmp_path / name).parent.mkdir(exist_ok=True)
        (tmp_path / name).write_text(content)
    found = None if child else _spy_find(monkeypatch)
    _check_chain(validation_for_path(tmp_path / "m.xml", trusted=True), found)


@pytest.mark.parametrize("child", [False, True])
def test_chained_sources_resolve_in_an_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, child: bool
) -> None:
    """A chain of external model definitions across the entries of an archive."""
    path = _archive(tmp_path / "chain.omex", _CHAIN, master="m.xml")
    found = None if child else _spy_find(monkeypatch)
    _check_chain(validation_for_path(path), found)


def test_every_entry_is_validated() -> None:
    """The neighbour which a trusted file names is validated as well."""
    response = validation_for_path(COMP_DELETION, trusted=True)
    assert len(response.entries) > 1
    for entry in response.entries.values():
        assert entry.skipped is None
        assert all(issue.pk for issue in entry.issues)


def test_the_entries_are_those_of_the_report(tmp_path: Path) -> None:
    """The validation has an entry per report of the source, in its order."""
    path = _archive(tmp_path / "chain.omex", _CHAIN, master="m.xml")
    assert list(validation_for_path(path).entries) == list(
        report_for_path(path).reports
    )


def test_the_report_carries_no_validation() -> None:
    """The report is built without the validation, which has endpoints of its own."""
    response = report_for_path(EXAMPLES_DIR / "validation.xml")
    data = response.model_dump(mode="json", by_alias=True)
    for entry in data["reports"].values():
        assert "validation" not in entry["report"]
        assert "validationSkipped" not in entry["report"]


def test_resolver_delegates_outside_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Outside of a validation libsbml resolves files as before, through the report."""
    registry = libsbml.SBMLResolverRegistry.getInstance()
    assert registry.getNumResolvers() == 1
    assert isinstance(_RESOLVER, ReportResolver)
    # the registry answers through the installed resolver, and the file resolver of
    # libsbml behind it answers a file
    calls: list[str] = []
    resolve_uri = ReportResolver.resolveUri

    def spy(
        self: ReportResolver, uri: str, baseUri: str = ""
    ) -> libsbml.SBMLUri | None:
        """Record the uri the registry asks the report resolver for."""
        calls.append(uri)
        return resolve_uri(self, uri, baseUri)

    monkeypatch.setattr(ReportResolver, "resolveUri", spy)
    uri = (EXAMPLES_DIR / "unit_definitions.xml").resolve().as_uri()
    resolved = registry.resolveUri(uri, "")
    assert calls == [uri]
    assert resolved is not None


# -------------------------------------------------------------------------------------
# the expanded-size budget
# -------------------------------------------------------------------------------------
# a parameter without units, which only the check of consistency reports
_UNITLESS = (
    '<listOfParameters><parameter id="p" value="1" constant="true"/></listOfParameters>'
)


def _submodels(model_ref: str, n: int) -> str:
    """A list of `n` submodels of one model."""
    return (
        "<comp:listOfSubmodels>"
        + "".join(
            f'<comp:submodel comp:id="s{i}" comp:modelRef="{model_ref}"/>'
            for i in range(n)
        )
        + "</comp:listOfSubmodels>"
    )


def _fan_out(depth: int, n: int = 10) -> bytes:
    """A document whose main model expands to `n` submodels on `depth` levels."""
    definitions = '<comp:modelDefinition id="d0"/>' + "".join(
        f'<comp:modelDefinition id="d{k}">{_submodels(f"d{k - 1}", n)}'
        "</comp:modelDefinition>"
        for k in range(1, depth)
    )
    return _COMP.format(
        f'<model id="m">{_UNITLESS}{_submodels(f"d{depth - 1}", n)}</model>'
        f"<comp:listOfModelDefinitions>{definitions}</comp:listOfModelDefinitions>"
    ).encode()


def _wide(instances: int, species: int = 20) -> bytes:
    """A main model of `instances` submodels of a definition of unitless species.

    With 1,000 instances of 20 species the document has 52 KB, and the check of
    its consistency takes more than 20 seconds and reports 41,043 issues.
    """
    definition = (
        '<comp:modelDefinition id="d"><listOfCompartments>'
        '<compartment id="c" constant="true"/></listOfCompartments><listOfSpecies>'
        + "".join(
            f'<species id="x{k}" compartment="c" initialAmount="1" '
            'hasOnlySubstanceUnits="true" boundaryCondition="false" '
            'constant="false"/>'
            for k in range(species)
        )
        + "</listOfSpecies></comp:modelDefinition>"
    )
    return _COMP.format(
        f'<model id="m">{_submodels("d", instances)}</model>'
        f"<comp:listOfModelDefinitions>{definition}</comp:listOfModelDefinitions>"
    ).encode()


def _info(content: bytes) -> SBMLDocumentInfo:
    """The report of a document, without its link graph."""
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(content.decode()))
    info.build_report()
    return info


def _size(info: SBMLDocumentInfo) -> int:
    """The expanded size of a single document."""
    return expanded_size({"d": info.report}, {"d": info.elements}, "d")


def test_the_elements_are_the_pks_of_the_report() -> None:
    """The elements counted per scope are the pks of the report."""
    info = _info(_fan_out(3))
    pks = _report_pks(info)
    scopes: dict[str, int] = {}
    for pk in pks:
        scope = pk.split("/", 1)[0]
        scopes[scope] = scopes.get(scope, 0) + 1
    assert dict(info.elements) == scopes


def test_expanded_size_counts_every_instance() -> None:
    """Every instance adds the elements of its model, along every level."""
    info = _info(_fan_out(3, n=4))
    sizes = {
        model.id: info.elements[model.pk.split("/", 1)[0]]
        for model in info.report.models
    }
    elements = sum(info.elements.values())
    # m has 4 instances of d2, each with 4 instances of d1, each with 4 of d0
    instances = 4 * (sizes["d2"] + 4 * (sizes["d1"] + 4 * sizes["d0"]))
    assert _size(info) == elements + instances


def test_expanded_size_of_a_flat_document_is_its_size() -> None:
    """A document without submodels expands to its own elements."""
    info = _info((EXAMPLES_DIR / "validation.xml").read_bytes())
    assert _size(info) == len(_report_pks(info))


def test_expanded_size_cuts_a_cycle() -> None:
    """A model which instantiates itself is counted once along its cycle."""
    content = _COMP.format(
        f'<model id="m">{_submodels("d", 2)}</model><comp:listOfModelDefinitions>'
        f'<comp:modelDefinition id="d">{_submodels("d", 2)}</comp:modelDefinition>'
        "</comp:listOfModelDefinitions>"
    )
    info = _info(content.encode())
    d = next(model for model in info.report.models if model.id == "d")
    size_d = info.elements[d.pk.split("/", 1)[0]]
    assert _size(info) == sum(info.elements.values()) + 2 * size_d


def test_wide_instantiation_beyond_the_budget_is_skipped_at_once() -> None:
    """The 52 KB document of 1,000 instances of 20 species is not validated."""
    content = _wide(1000)
    assert 50_000 < len(content) < 60_000
    assert _size(_info(content)) > MAX_EXPANDED_ELEMENTS
    start = time.perf_counter()
    entry = _entry(validation_for_bytes(content))
    elapsed = time.perf_counter() - start
    assert entry.skipped == "expandedSize"
    assert entry.issues == []
    assert elapsed < 1.0


def test_submodel_fan_out_beyond_the_budget_is_skipped() -> None:
    """A document which expands to 111,110 instances is answered at once."""
    start = time.perf_counter()
    entry = _entry(validation_for_bytes(_fan_out(5)))
    elapsed = time.perf_counter() - start
    assert entry.skipped == "expandedSize"
    assert 80701 not in {issue.rule for issue in entry.issues}
    assert elapsed < 1.0


def test_read_errors_are_reported_without_validation() -> None:
    """A document which is not validated still has the read errors of libsbml."""
    content = _fan_out(5).replace(b'<model id="m">', b'<model id="m" foo="1">')
    entry = _entry(validation_for_bytes(content))
    assert entry.skipped == "expandedSize"
    assert 20222 in {issue.rule for issue in entry.issues}


def test_a_document_at_the_budget_is_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    """The budget is the largest expanded size which is validated."""
    content = _wide(30)
    size = _size(_info(content))
    monkeypatch.setattr(validation, "MAX_EXPANDED_ELEMENTS", size)
    entry = _entry(validation_for_bytes(content))
    assert entry.skipped is None
    assert 20616 in {issue.rule for issue in entry.issues}
    monkeypatch.setattr(validation, "MAX_EXPANDED_ELEMENTS", size - 1)
    assert _entry(validation_for_bytes(content)).skipped == "expandedSize"


def test_submodel_fan_out_within_the_budget_is_validated() -> None:
    """A document which expands to 110 instances is validated."""
    entry = _entry(validation_for_bytes(_fan_out(2)))
    assert entry.skipped is None
    assert 80701 in {issue.rule for issue in entry.issues}


def _archive(path: Path, documents: dict[str, str], master: str | None = None) -> Path:
    """A COMBINE archive of SBML documents, the first one the master by default."""
    master = master or next(iter(documents))
    entries = "".join(
        f'<content location="./{name}" '
        'format="http://identifiers.org/combine.specifications/sbml" '
        f'master="{str(name == master).lower()}"/>'
        for name in documents
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "manifest.xml",
            '<omexManifest xmlns="http://identifiers.org/combine.specifications/'
            f'omex-manifest">{entries}</omexManifest>',
        )
        for name, content in documents.items():
            archive.writestr(name, content)
    return path


def test_archive_chain_beyond_the_budget_is_not_validated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Instances through external model definitions of other entries count."""

    def link(target: str) -> str:
        """A main model of 10 submodels of the main model of `target`."""
        return f'<model id="m">{_UNITLESS}{_submodels("x", 10)}</model>' + _emds(
            ("x", target, "m")
        )

    documents = {
        "a.xml": _COMP.format(link("b.xml")),
        "b.xml": _COMP.format(link("c.xml")),
        "c.xml": _COMP.format(link("d.xml")),
        "d.xml": _COMP.format(f'<model id="m">{_UNITLESS}</model>'),
    }
    path = _archive(tmp_path / "chain.omex", documents)
    # a expands to about 4,700 elements, b to 500, c to 70 and d to 4
    monkeypatch.setattr(validation, "MAX_EXPANDED_ELEMENTS", 1000)
    response = validation_for_path(path)
    skipped = {location: entry.skipped for location, entry in response.entries.items()}
    assert skipped == {
        "./a.xml": "expandedSize",
        "./b.xml": None,
        "./c.xml": None,
        "./d.xml": None,
    }
    assert 80701 in {i.rule for i in response.entries["./b.xml"].issues}


def test_validate_entries_in_this_process() -> None:
    """What the child process runs: the issues of every target, in order."""
    info = _info((EXAMPLES_DIR / "validation.xml").read_bytes())
    job = validation.ValidationJob(
        paths={"./model.xml": str(EXAMPLES_DIR / "validation.xml")},
        targets={"./model.xml": info.positions},
    )
    results = list(validate_entries(job))
    assert [location for location, _ in results] == ["./model.xml"]
    assert 10601 in {issue.rule for issue in results[0][1]}


# -------------------------------------------------------------------------------------
# the child process: timeout, memory and concurrency
# -------------------------------------------------------------------------------------
def _slow(monkeypatch: pytest.MonkeyPatch) -> bytes:
    """A document whose validation takes more than 20 seconds, without the budget."""
    monkeypatch.setattr(validation, "MAX_EXPANDED_ELEMENTS", 10**9)
    return _wide(1000)


def _spy_children(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Record the pid of every child process the validation starts."""
    pids: list[int] = []
    start = isolation._start

    def spy(*args: Any) -> Any:
        process = start(*args)
        assert process.pid is not None
        pids.append(process.pid)
        return process

    monkeypatch.setattr(isolation, "_start", spy)
    return pids


def _gone(pid: int) -> bool:
    """Whether no process of the pid runs any more."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def test_timeout_terminates_the_child(monkeypatch: pytest.MonkeyPatch) -> None:
    """A validation beyond the timeout is ended and its entry skipped."""
    content = _slow(monkeypatch)
    monkeypatch.setattr(isolation, "VALIDATION_TIMEOUT", 1.0)
    pids = _spy_children(monkeypatch)
    start = time.perf_counter()
    entry = _entry(validation_for_bytes(content))
    elapsed = time.perf_counter() - start
    assert entry.skipped == "timeout"
    assert entry.issues == []
    assert elapsed < 3.0
    assert len(pids) == 1
    assert _gone(pids[0])


def test_timeout_keeps_the_entries_validated_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The entries the child validated before the timeout keep their issues."""
    content = _slow(monkeypatch)
    monkeypatch.setattr(isolation, "VALIDATION_TIMEOUT", 2.0)
    documents = {
        "a.xml": (EXAMPLES_DIR / "validation.xml").read_text(),
        "b.xml": content.decode(),
    }
    response = validation_for_path(_archive(tmp_path / "slow.omex", documents))
    assert response.entries["./a.xml"].skipped is None
    assert 10601 in {i.rule for i in response.entries["./a.xml"].issues}
    assert response.entries["./b.xml"].skipped == "timeout"


def _flat(species: int) -> bytes:
    """A document of a model with many species, which take memory to read."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" '
        'version="1"><model id="m"><listOfCompartments>'
        '<compartment id="c" constant="true"/></listOfCompartments><listOfSpecies>'
        + "".join(
            f'<species id="x{k}" compartment="c" initialAmount="1" '
            'hasOnlySubstanceUnits="true" boundaryCondition="false" '
            'constant="false"/>'
            for k in range(species)
        )
        + "</listOfSpecies></model></sbml>"
    ).encode()


def test_a_flat_document_beyond_the_budget_is_validated() -> None:
    """The budget counts instances, a document without them is always checked."""
    content = _flat(MAX_EXPANDED_ELEMENTS + 100)
    assert _size(_info(content)) > MAX_EXPANDED_ELEMENTS
    entry = _entry(validation_for_bytes(content))
    assert entry.skipped is None
    assert 20616 in {issue.rule for issue in entry.issues}


def test_memory_limit_skips_the_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    """A validation beyond the memory limit is skipped, the parent answers."""
    content = _flat(20_000)
    # the address space of the child is far beyond the limit already, so every
    # page it maps from now on fails
    monkeypatch.setattr(isolation, "VALIDATION_MEMORY", 1024 * 1024)
    monkeypatch.setattr(isolation, "VALIDATION_TIMEOUT", 20.0)
    pids = _spy_children(monkeypatch)
    entry = _entry(validation_for_bytes(content))
    assert entry.skipped == "memory"
    assert entry.issues == []
    assert _gone(pids[0])


def test_validation_within_the_memory_limit() -> None:
    """The default limit leaves room for the validation."""
    entry = _entry(validation_for_path(EXAMPLES_DIR / "validation.xml"))
    assert entry.skipped is None
    assert entry.issues


@pytest.mark.parametrize("limit", [1, 2])
def test_semaphore_bounds_the_children(
    monkeypatch: pytest.MonkeyPatch, limit: int
) -> None:
    """At most `MAX_CONCURRENT_VALIDATIONS` children run at a time."""
    monkeypatch.setattr(isolation, "MAX_CONCURRENT_VALIDATIONS", limit)
    running = 0
    most = 0
    lock = threading.Lock()
    run_child = isolation._run_child

    def spy(*args: Any) -> Any:
        """Count the children which run, each for at least a little while."""
        nonlocal running, most
        with lock:
            running += 1
            most = max(most, running)
        try:
            time.sleep(0.5)
            return run_child(*args)
        finally:
            with lock:
                running -= 1

    monkeypatch.setattr(isolation, "_run_child", spy)
    content = (EXAMPLES_DIR / "validation.xml").read_bytes()
    results: list[ValidationResponse] = []
    threads = [
        threading.Thread(target=lambda: results.append(validation_for_bytes(content)))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert most == limit
    assert [_entry(r).skipped for r in results] == [None, None]


def test_waiting_counts_against_the_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """A request which waits for a child longer than its timeout is skipped."""
    monkeypatch.setattr(isolation, "MAX_CONCURRENT_VALIDATIONS", 1)
    monkeypatch.setattr(isolation, "VALIDATION_TIMEOUT", 1.0)
    pids = _spy_children(monkeypatch)
    # another request holds the one child
    semaphore = isolation._semaphore()
    semaphore.acquire()
    try:
        start = time.perf_counter()
        entry = _entry(validation_for_path(EXAMPLES_DIR / "validation.xml"))
        elapsed = time.perf_counter() - start
    finally:
        semaphore.release()
    assert entry.skipped == "timeout"
    assert 1.0 <= elapsed < 2.0
    assert pids == []


def test_a_document_without_a_model_is_an_error() -> None:
    """The validation of a source without a model fails like its report."""
    content = _COMP.format("").encode()
    with pytest.raises(ValueError, match="No SBML model"):
        validation_for_bytes(content)
    with pytest.raises(ValueError, match="No SBML model"):
        report_for_bytes(content)


def test_an_unexpected_end_of_the_child_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A child which ends without a result and without a known cause fails."""
    monkeypatch.setattr(report, "validate_entries", _crash)
    with pytest.raises(isolation.ValidationProcessError, match="ended unexpectedly"):
        validation_for_path(EXAMPLES_DIR / "validation.xml")


def _crash(job: validation.ValidationJob) -> Iterator[tuple[str, list[Any]]]:
    """End the child process by a signal no limit sends."""
    os.kill(os.getpid(), signal.SIGSEGV)
    yield from ()
