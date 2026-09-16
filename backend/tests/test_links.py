"""Tests of the link graph."""

import logging

import pytest

from sbml4humans.model import Edge, EdgeKind, Report
from sbml4humans.resources import (
    COMP_ICG_BODY,
    EXAMPLES_DIR,
    FBC_ECOLI_CORE_SBML,
    REPRESSILATOR_SBML,
)
from sbml4humans.sbmlinfo import SBMLDocumentInfo


def _edges(
    report: Report, source: str | None = None, kind: EdgeKind | None = None
) -> set[tuple[str, str, str]]:
    """The edges of the report as tuples, filtered by source and kind."""
    return {
        (e.source, e.target, e.kind.value)
        for e in report.link_graph.edges
        if (source is None or e.source == source) and (kind is None or e.kind == kind)
    }


@pytest.fixture(scope="module")
def repressilator() -> Report:
    """The report of the repressilator."""
    return SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)


def test_every_sbase_is_a_node(repressilator: Report) -> None:
    """Document, model, elements and nested elements are nodes."""
    nodes = repressilator.link_graph.nodes
    model = repressilator.models[0]
    assert repressilator.document.pk in nodes
    assert model.pk in nodes
    assert nodes[model.pk].model is None
    species = model.list_of_species[0]
    assert nodes[species.pk].model == model.pk
    assert nodes[species.pk].sbml_type == "Species"
    reaction = model.list_of_reactions[0]
    assert reaction.list_of_reactants[0].pk in nodes
    assert reaction.kinetic_law is not None
    assert reaction.kinetic_law.pk in nodes


def test_edges_reference_nodes(repressilator: Report) -> None:
    """Every edge connects two existing nodes."""
    nodes = repressilator.link_graph.nodes
    for edge in repressilator.link_graph.edges:
        assert edge.source in nodes
        assert edge.target in nodes


def test_reaction_edges(repressilator: Report) -> None:
    """A reaction links to its species and the symbols of its kinetic law."""
    m = "BIOMD0000000012"
    reaction = f"{m}/Reaction:Reaction1"
    assert _edges(repressilator, source=reaction) == {
        (reaction, f"{m}/Species:X", "reactant"),
    }
    kinetic_law = repressilator.models[0].list_of_reactions[0].kinetic_law
    assert kinetic_law is not None
    assert _edges(repressilator, source=kinetic_law.pk) == {
        (kinetic_law.pk, f"{m}/Parameter:kd_mRNA", "math"),
        (kinetic_law.pk, f"{m}/Species:X", "math"),
    }


def test_species_and_rule_edges(repressilator: Report) -> None:
    """Species link to their compartment, rules to their variable and symbols."""
    m = "BIOMD0000000012"
    assert (f"{m}/Species:PX", f"{m}/Compartment:cell", "compartment") in _edges(
        repressilator
    )
    variable_edges = _edges(repressilator, kind=EdgeKind.VARIABLE)
    assert len(variable_edges) == 9
    assert all(t.startswith(f"{m}/Parameter:") for _, t, _ in variable_edges)
    assert _edges(repressilator, kind=EdgeKind.MATH)


def test_units_edges() -> None:
    """Units attributes link to the unit definitions of the model."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "reaction_with_units.xml")
    m = "reaction_with_units"
    units_edges = _edges(report, kind=EdgeKind.UNITS)
    assert units_edges
    assert all(t.startswith(f"{m}/UnitDefinition:") for _, t, _ in units_edges)


def test_comp_edges() -> None:
    """Submodels, ports and replacements are edges."""
    report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    m = "icg_body"
    assert (
        f"{m}/Submodel:LI",
        "document/ExternalModelDefinition:liver",
        "modelRef",
    ) in _edges(report)
    assert (
        f"{m}/Port:Vre_tissue_port",
        f"{m}/Compartment:Vre_tissue",
        "port",
    ) in _edges(report)
    assert (
        f"{m}/Species:Cli_plasma_icg",
        f"{m}/Submodel:LI",
        "replacedElement",
    ) in _edges(report)


def test_fbc_edges() -> None:
    """Flux bounds, gene products, associated species and objectives are edges."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    m = "e_coli_core"
    reaction = f"{m}/Reaction:R_PFK"
    edges = _edges(report, source=reaction)
    assert (reaction, f"{m}/Parameter:cobra_0_bound", "fluxBound") in edges
    assert (reaction, f"{m}/Parameter:cobra_default_ub", "fluxBound") in edges
    assert (reaction, f"{m}/GeneProduct:G_b3916", "geneProduct") in edges
    assert (
        f"{m}/Objective:obj",
        f"{m}/Reaction:R_BIOMASS_Ecoli_core_w_GAM",
        "fluxObjective",
    ) in _edges(report)


def test_dangling_reference_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    """An unresolvable reference produces no edge and a warning."""
    sbml = """<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
      <model id="m">
        <listOfCompartments><compartment id="c" constant="true"/></listOfCompartments>
        <listOfSpecies><species id="s" compartment="missing" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/></listOfSpecies>
      </model>
    </sbml>"""
    with caplog.at_level(logging.WARNING, logger="sbml4humans.links"):
        report = SBMLDocumentInfo.from_sbml(sbml)
    assert _edges(report, kind=EdgeKind.COMPARTMENT) == set()
    assert "missing" in caplog.text


def test_edge_is_hashable_value() -> None:
    """Edges compare by value."""
    assert Edge(source="a", target="b", kind=EdgeKind.MATH) == Edge(
        source="a", target="b", kind=EdgeKind.MATH
    )
