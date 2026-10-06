"""The differential equations of a model in its report, `Report.ode_system`."""

from pathlib import Path

import libsbml
import pytest
import sbmlode

from sbml4humans.model import Report
from sbml4humans.report import report_for_bytes, report_for_path
from sbml4humans.resources import EXAMPLES_DIR, REPRESSILATOR_SBML


def _report_of_path(path: Path) -> Report:
    """The report of the single document of a path."""
    response = report_for_path(path, trusted=True)
    return next(iter(response.reports.values())).report


def _report_of_doc(doc: libsbml.SBMLDocument) -> Report:
    """The report of a document."""
    response = report_for_bytes(libsbml.writeSBMLToString(doc).encode())
    return next(iter(response.reports.values())).report


def _document() -> tuple[libsbml.SBMLDocument, libsbml.Model]:
    """A document with a model `m`: compartment c, species S, reaction J0: S ->."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId("m")
    c: libsbml.Compartment = model.createCompartment()
    c.setId("c")
    c.setSize(1.0)
    c.setConstant(True)
    s: libsbml.Species = model.createSpecies()
    s.setId("S")
    s.setCompartment("c")
    s.setInitialConcentration(10.0)
    s.setHasOnlySubstanceUnits(False)
    s.setBoundaryCondition(False)
    s.setConstant(False)
    r: libsbml.Reaction = model.createReaction()
    r.setId("J0")
    r.setReversible(False)
    reactant: libsbml.SpeciesReference = r.createReactant()
    reactant.setSpecies("S")
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    law: libsbml.KineticLaw = r.createKineticLaw()
    law.setMath(libsbml.parseL3Formula("k * S"))
    k: libsbml.LocalParameter = law.createLocalParameter()
    k.setId("k")
    k.setValue(0.1)
    return doc, model


def test_repressilator_system() -> None:
    """The ODEs, rates and rules of the repressilator, every symbol linked."""
    report = _report_of_path(REPRESSILATOR_SBML)
    ode = report.ode_system
    assert ode is not None
    assert report.ode_error is None
    assert (len(ode.odes), len(ode.reactions), len(ode.assignments)) == (6, 12, 9)
    first = ode.odes[0]
    assert first.variable == "BIOMD0000000012/Species:PX"
    assert first.origin == "reactions"
    assert r"\htmlData{pk=BIOMD0000000012/Species:PX}" in first.lhs
    assert first.lines == [
        r"\htmlData{pk=BIOMD0000000012/Reaction:Reaction4}{v_{\mathrm{Reaction4}}} - "
        r"\htmlData{pk=BIOMD0000000012/Reaction:Reaction7}{v_{\mathrm{Reaction7}}}"
    ]
    rate = ode.reactions[0]
    assert rate.variable == "BIOMD0000000012/Reaction:Reaction1"
    assert rate.origin == "reaction"
    assert r"\htmlData{pk=BIOMD0000000012/Parameter:kd_mRNA}" in rate.lines[0]
    assert ode.assignments[0].origin == "assignment_rule"
    assert ode.unsupported == []


def test_json_is_camel_case() -> None:
    """The report states the system as `odeSystem` and its failure as `odeError`."""
    report = _report_of_path(REPRESSILATOR_SBML)
    data = report.model_dump(mode="json", by_alias=True)
    assert set(data["odeSystem"]) == {
        "odes",
        "reactions",
        "assignments",
        "functions",
        "initial",
        "events",
        "unsupported",
    }
    assert data["odeError"] is None


def test_local_parameter_links_to_its_kinetic_law() -> None:
    """A local parameter, which sbmlode renames, links to the local parameter."""
    doc, _ = _document()
    report = _report_of_doc(doc)
    ode = report.ode_system
    assert ode is not None
    law = report.models[0].list_of_reactions[0].kinetic_law
    assert law is not None
    local_pk = law.list_of_local_parameters[0].pk
    assert rf"\htmlData{{pk={local_pk}}}" in ode.reactions[0].lines[0]
    assert ode.odes[0].variable == "m/Species:S"


def test_algebraic_rule_is_unsupported() -> None:
    """An algebraic rule is reported as unsupported.

    Without an id or a metaid, which sbmlode could name, it is not linked.
    """
    report = _report_of_path(EXAMPLES_DIR / "algebraic_rule.xml")
    ode = report.ode_system
    assert ode is not None
    assert [(u.kind, u.element) for u in ode.unsupported] == [("algebraic rule", None)]


def test_algebraic_rule_with_metaid_is_linked() -> None:
    """An algebraic rule with a metaid links to its element."""
    doc, model = _document()
    rule: libsbml.AlgebraicRule = model.createAlgebraicRule()
    rule.setMetaId("rule_meta")
    rule.setMath(libsbml.parseL3Formula("S - 1"))
    report = _report_of_doc(doc)
    ode = report.ode_system
    assert ode is not None
    pk = report.models[0].list_of_rules[0].pk
    assert [(u.kind, u.element) for u in ode.unsupported] == [("algebraic rule", pk)]


def _comp_document(source: str) -> libsbml.SBMLDocument:
    """A document whose model instantiates the model `m` of an external `source`."""
    doc = libsbml.SBMLDocument(3, 1)
    doc.enablePackage(libsbml.CompExtension.getXmlnsL3V1V1(), "comp", True)
    doc.setPackageRequired("comp", True)
    model: libsbml.Model = doc.createModel()
    model.setId("top")
    comp_doc: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    emd: libsbml.ExternalModelDefinition = comp_doc.createExternalModelDefinition()
    emd.setId("ext")
    emd.setSource(source)
    emd.setModelRef("m")
    comp_model: libsbml.CompModelPlugin = model.getPlugin("comp")
    submodel: libsbml.Submodel = comp_model.createSubmodel()
    submodel.setId("sub")
    submodel.setModelRef("ext")
    return doc


def test_external_model_of_a_request_reads_no_file(tmp_path: Path) -> None:
    """The flattening resolves an external model within the report, never a file.

    The content of a request names a file of the server by its absolute path; the
    analysis fails rather than read it, and nothing of the file is in the report.
    """
    secret, _ = _document()
    secret.getModel().getSpecies("S").setId("secret_species")
    secret.getModel().getReaction("J0").getReactant(0).setSpecies("secret_species")
    law = secret.getModel().getReaction("J0").getKineticLaw()
    law.setMath(libsbml.parseL3Formula("k * secret_species"))
    # comp resolves an external model of the level and version of the document
    assert secret.setLevelAndVersion(3, 1, False)
    path = tmp_path / "secret.xml"
    libsbml.writeSBMLToFile(secret, str(path))
    report = _report_of_doc(_comp_document(str(path)))
    assert report.ode_system is None
    assert report.ode_error is not None
    dumped = report.model_dump_json()
    assert "secret_species" not in dumped


def test_flattened_symbol_is_not_linked() -> None:
    """A symbol the flattening of comp makes up has no element and is no link."""
    report = _report_of_path(EXAMPLES_DIR / "minimal_model_comp.xml")
    ode = report.ode_system
    assert ode is not None
    flattened = [
        line for eq in ode.assignments + ode.odes for line in [eq.lhs, *eq.lines]
    ]
    text = " ".join(flattened)
    assert "submodel0" in text
    assert "pk=minimal_model_comp/Species:submodel0__S2" not in text


def test_analysis_error_is_contained(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failure of the analysis is its message, the rest of the report is there."""

    def boom(source: object) -> object:
        raise ValueError("the analysis failed")

    monkeypatch.setattr(sbmlode.OdeSystem, "from_sbml", staticmethod(boom))
    report = _report_of_path(REPRESSILATOR_SBML)
    assert report.ode_system is None
    assert report.ode_error == "the analysis failed"
    assert report.models[0].list_of_species
