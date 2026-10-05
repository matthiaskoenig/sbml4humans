"""Tests of the validation of a document and the mapping of its issues."""

import http.server
import threading
import time
import zipfile
from pathlib import Path

import libsbml
import pytest

from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_bytes, report_for_path
from sbml4humans.resources import EXAMPLES_DIR
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.validation import (
    _RESOLVER,
    ElementPositions,
    ReportDocuments,
    ReportResolver,
    issues_of,
    submodel_instances,
    validate,
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
    report = next(iter(report_for_path(EXAMPLES_DIR / "reaction.xml").reports.values()))
    units = {
        (issue.rule, issue.severity, issue.pk)
        for issue in report.report.validation
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
    report = next(iter(report_for_bytes(content).reports.values())).report
    comp = {
        (issue.rule, issue.severity, issue.pk)
        for issue in report.validation
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


def _rules(response: ReportResponse, location: str | None = None) -> set[int]:
    """The rules of the issues of an entry of a response, the first by default."""
    entries = response.reports
    entry = entries[location] if location else next(iter(entries.values()))
    return {issue.rule for issue in entry.report.validation}


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
            response = report_for_bytes(content.encode())
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
    """Record every request of the resolver: source, base and the found model."""
    found: list[tuple[str, str | None, str]] = []
    find = ReportDocuments.find

    def spy(
        self: ReportDocuments, source: str, base: str | None
    ) -> libsbml.SBMLDocument | None:
        doc = find(self, source, base)
        found.append((source, base, doc.getModel().getId() if doc else ""))
        return doc

    monkeypatch.setattr(ReportDocuments, "find", spy)
    return found


def test_trusted_neighbour_is_resolved_from_the_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A source the report read is resolved for the validation, without 1090101."""
    found = _spy_find(monkeypatch)
    response = report_for_path(COMP_DELETION, trusted=True)
    assert "./unit_definitions.xml" in response.reports
    assert ("unit_definitions.xml", "./comp_deletion.xml", "unit_definitions") in found
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
    response: ReportResponse, found: list[tuple[str, str | None, str]]
) -> None:
    """The chain is resolved within the report, each source against its base."""
    assert {"./m.xml", "./sub/b.xml", "./sub/c.xml", "./c.xml"} <= set(response.reports)
    for location, entry in response.reports.items():
        rules = {issue.rule for issue in entry.report.validation}
        assert not rules & _UNRESOLVED, location
    assert ("c.xml", "sub/b.xml", "C") in found
    assert ("c.xml", "./m.xml", "W") in found
    assert {model for source, _, model in found if source == "c.xml"} == {"C", "W"}


def test_chained_sources_resolve_against_their_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A chain of external model definitions of trusted files is followed."""
    for name, content in _CHAIN.items():
        (tmp_path / name).parent.mkdir(exist_ok=True)
        (tmp_path / name).write_text(content)
    found = _spy_find(monkeypatch)
    _check_chain(report_for_path(tmp_path / "m.xml", trusted=True), found)


def test_chained_sources_resolve_in_an_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A chain of external model definitions across the entries of an archive."""
    path = tmp_path / "chain.omex"
    entries = "".join(
        f'<content location="./{name}" '
        'format="http://identifiers.org/combine.specifications/sbml" '
        f'master="{str(name == "m.xml").lower()}"/>'
        for name in _CHAIN
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "manifest.xml",
            '<omexManifest xmlns="http://identifiers.org/combine.specifications/'
            f'omex-manifest">{entries}</omexManifest>',
        )
        for name, content in _CHAIN.items():
            archive.writestr(name, content)
    found = _spy_find(monkeypatch)
    _check_chain(report_for_path(path), found)


def test_every_entry_is_validated() -> None:
    """The neighbour which a trusted file names is validated as well."""
    response = report_for_path(COMP_DELETION, trusted=True)
    assert len(response.reports) > 1
    for entry in response.reports.values():
        assert all(issue.pk for issue in entry.report.validation)


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


def test_submodel_fan_out_beyond_the_budget_is_not_validated() -> None:
    """A document which expands to 111,110 instances is reported at once."""
    start = time.perf_counter()
    response = report_for_bytes(_fan_out(5))
    elapsed = time.perf_counter() - start
    report = next(iter(response.reports.values())).report
    assert report.validation_skipped == "submodelInstances"
    assert 80701 not in {issue.rule for issue in report.validation}
    assert elapsed < 0.5


def test_read_errors_are_reported_without_validation() -> None:
    """A document which is not validated still has the read errors of libsbml."""
    content = _fan_out(5).replace(b'<model id="m">', b'<model id="m" foo="1">')
    report = next(iter(report_for_bytes(content).reports.values())).report
    assert report.validation_skipped == "submodelInstances"
    assert 20222 in {issue.rule for issue in report.validation}


def test_submodel_fan_out_within_the_budget_is_validated() -> None:
    """A document which expands to 110 instances is validated."""
    report = next(iter(report_for_bytes(_fan_out(2)).reports.values()))
    assert report.report.validation_skipped is None
    assert 80701 in {issue.rule for issue in report.report.validation}


def test_submodel_instances_cut_a_cycle() -> None:
    """A model which instantiates itself is counted once along its cycle."""
    content = _COMP.format(
        f'<model id="m">{_submodels("d", 2)}</model><comp:listOfModelDefinitions>'
        f'<comp:modelDefinition id="d">{_submodels("d", 2)}</comp:modelDefinition>'
        "</comp:listOfModelDefinitions>"
    )
    response = report_for_bytes(content.encode())
    reports = {location: e.report for location, e in response.reports.items()}
    assert submodel_instances(reports, next(iter(reports))) == 6


def _archive(path: Path, documents: dict[str, str]) -> Path:
    """A COMBINE archive of SBML documents, the first one the master."""
    entries = "".join(
        f'<content location="./{name}" '
        'format="http://identifiers.org/combine.specifications/sbml" '
        f'master="{str(k == 0).lower()}"/>'
        for k, name in enumerate(documents)
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


def test_archive_chain_beyond_the_budget_is_not_validated(tmp_path: Path) -> None:
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
    response = report_for_path(_archive(tmp_path / "chain.omex", documents))
    skipped = {
        location: entry.report.validation_skipped
        for location, entry in response.reports.items()
    }
    # a: 10 + 100 + 1,000 instances, b: 10 + 100, c: 10, d: none
    assert skipped == {
        "./a.xml": "submodelInstances",
        "./b.xml": None,
        "./c.xml": None,
        "./d.xml": None,
    }
    assert 80701 in {i.rule for i in response.reports["./b.xml"].report.validation}
