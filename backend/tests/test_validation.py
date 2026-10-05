"""Tests of the validation of a document and the mapping of its issues."""

import libsbml
import pytest

from sbml4humans.resources import EXAMPLES_DIR
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.validation import ElementPositions, issues_of


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
