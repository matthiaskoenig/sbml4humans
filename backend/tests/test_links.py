"""Tests of the link graph."""

import logging

import libsbml
import pytest

from sbml4humans.links import build_link_graph
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


@pytest.fixture(scope="module")
def comp_deletion() -> Report:
    """The report of the deletion and replacement example of comp."""
    return SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "comp_deletion.xml")


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
    """A reaction links to its participants and its kinetic law to its symbols."""
    m = "BIOMD0000000012"
    reaction = repressilator.models[0].list_of_reactions[0]
    assert reaction.pk == f"{m}/Reaction:Reaction1"
    reactant = reaction.list_of_reactants[0]
    assert _edges(repressilator, source=reaction.pk) == {
        (reaction.pk, reactant.pk, "reactant"),
    }
    kinetic_law = reaction.kinetic_law
    assert kinetic_law is not None
    assert _edges(repressilator, source=kinetic_law.pk) == {
        (kinetic_law.pk, f"{m}/Parameter:kd_mRNA", "math"),
        (kinetic_law.pk, f"{m}/Species:X", "math"),
    }


def test_species_reference_edges(repressilator: Report) -> None:
    """The reference to a species starts at the species reference which names it.

    The reaction names its reactants, its products and its modifiers, and each
    of them names one species (core §4.11.1-4), so the two hops of one kind
    lead from a reaction to the species it consumes and back.
    """
    m = "BIOMD0000000012"
    model = repressilator.models[0]
    reactant = model.list_of_reactions[0].list_of_reactants[0]
    assert _edges(repressilator, source=reactant.pk) == {
        (reactant.pk, f"{m}/Species:X", "reactant"),
    }
    with_product = next(r for r in model.list_of_reactions if r.list_of_products)
    product = with_product.list_of_products[0]
    assert (with_product.pk, product.pk, "product") in _edges(repressilator)
    assert (product.pk, f"{m}/Species:{product.species}", "product") in _edges(
        repressilator
    )
    with_modifier = next(r for r in model.list_of_reactions if r.list_of_modifiers)
    modifier = with_modifier.list_of_modifiers[0]
    assert (with_modifier.pk, modifier.pk, "modifier") in _edges(repressilator)
    assert (modifier.pk, f"{m}/Species:{modifier.species}", "modifier") in _edges(
        repressilator
    )


def test_no_species_reference_is_isolated(repressilator: Report) -> None:
    """Every species reference of a model is part of the graph."""
    graph = repressilator.link_graph
    connected = {e.source for e in graph.edges} | {e.target for e in graph.edges}
    references = [
        node
        for node in graph.nodes.values()
        if node.sbml_type in {"SpeciesReference", "ModifierSpeciesReference"}
    ]
    assert len(references) == 18
    assert [node.pk for node in references if node.pk not in connected] == []


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
    replaced = f"{m}/ReplacedElement:Cli_plasma_icg_RE"
    assert (f"{m}/Species:Cli_plasma_icg", replaced, "replacedElement") in _edges(
        report
    )


def test_fbc_edges() -> None:
    """Flux bounds, gene products and objectives are edges."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    m = "e_coli_core"
    reaction = f"{m}/Reaction:R_PFK"
    edges = _edges(report, source=reaction)
    assert (reaction, f"{m}/Parameter:cobra_0_bound", "fluxBound") in edges
    assert (reaction, f"{m}/Parameter:cobra_default_ub", "fluxBound") in edges
    flux_objective = f"{m}/FluxObjective:obj.fluxObjective.R_BIOMASS_Ecoli_core_w_GAM"
    assert (f"{m}/Objective:obj", flux_objective, "fluxObjective") in _edges(report)
    assert (
        flux_objective,
        f"{m}/Reaction:R_BIOMASS_Ecoli_core_w_GAM",
        "fluxObjective",
    ) in _edges(report)


def test_gene_product_edge_starts_at_the_reference() -> None:
    """The reaction names its association, and the reference names the gene product."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    m = "e_coli_core"
    association = f"{m}/GeneProductAssociation:R_PFK.geneProductAssociation"
    node = f"{m}/Or:R_PFK.geneProductAssociation.association"
    first = f"{m}/GeneProductRef:R_PFK.geneProductAssociation.association.0"
    assert _edges(
        report,
        source=f"{m}/Reaction:R_PFK",
        kind=EdgeKind.GENE_PRODUCT_ASSOCIATION,
    ) == {
        (f"{m}/Reaction:R_PFK", association, "geneProductAssociation"),
    }
    assert (association, node, "geneProductAssociation") in _edges(report)
    assert (node, first, "geneProductAssociation") in _edges(report)
    assert _edges(report, source=first) == {
        (first, f"{m}/GeneProduct:G_b3916", "geneProduct"),
    }
    # no reaction names a gene product itself any more
    assert not [
        edge
        for edge in report.link_graph.edges
        if edge.kind == EdgeKind.GENE_PRODUCT
        and report.link_graph.nodes[edge.source].sbml_type != "GeneProductRef"
    ]


def test_association_nodes_are_connected() -> None:
    """Every node of every association tree carries an edge in both directions."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    types = {"GeneProductAssociation", "And", "Or", "GeneProductRef"}
    nodes = [n for n in report.link_graph.nodes.values() if n.sbml_type in types]
    assert len(nodes) == 8
    sources = {edge.source for edge in report.link_graph.edges}
    targets = {edge.target for edge in report.link_graph.edges}
    assert all(node.pk in sources and node.pk in targets for node in nodes)


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


def test_edge_is_hashable() -> None:
    """Edges compare by value and equal edges have equal hashes."""
    edge = Edge(source="a", target="b", kind=EdgeKind.MATH)
    same = Edge(source="a", target="b", kind=EdgeKind.MATH)
    assert edge == same
    assert hash(edge) == hash(same)
    assert len({edge, same}) == 1


# -------------------------------------------------------------------------------------
# synthetic models: one reference kind per model, built as SBML string
# -------------------------------------------------------------------------------------
def _mathml(formula: str) -> str:
    """The content MathML of an L3 formula, for embedding in an SBML string."""
    astnode = libsbml.parseL3Formula(formula)
    assert astnode is not None, libsbml.getLastParseL3Error()
    xml: str = libsbml.writeMathMLToString(astnode)
    return xml.replace('<?xml version="1.0" encoding="UTF-8"?>', "").strip()


SYNTHETIC_FBC_SBML = f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2"
      level="3" version="1" fbc:required="false">
  <model id="synth" conversionFactor="cf" fbc:strict="false">
    <listOfFunctionDefinitions>
      <functionDefinition id="f">{_mathml("lambda(x, x * k)")}</functionDefinition>
    </listOfFunctionDefinitions>
    <listOfCompartments>
      <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="s" compartment="c" initialAmount="1" hasOnlySubstanceUnits="false"
               boundaryCondition="false" constant="false" conversionFactor="cf_s"/>
    </listOfSpecies>
    <listOfParameters>
      <parameter id="x" value="1" constant="true"/>
      <parameter id="k" value="2" constant="true"/>
      <parameter id="cf" value="1" constant="true"/>
      <parameter id="cf_s" value="1" constant="true"/>
    </listOfParameters>
    <listOfInitialAssignments>
      <initialAssignment symbol="s">{_mathml("k")}</initialAssignment>
    </listOfInitialAssignments>
    <listOfReactions>
      <reaction id="r" reversible="false" fast="false">
        <listOfReactants>
          <speciesReference species="s" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <kineticLaw>
          {_mathml("k * s")}
          <listOfLocalParameters>
            <localParameter id="k" value="3"/>
          </listOfLocalParameters>
        </kineticLaw>
      </reaction>
    </listOfReactions>
    <fbc:listOfGeneProducts>
      <fbc:geneProduct fbc:id="g" fbc:label="g" fbc:associatedSpecies="s"/>
    </fbc:listOfGeneProducts>
  </model>
</sbml>"""

SYNTHETIC_COMP_SBML = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1"
      level="3" version="1" comp:required="true">
  <model id="top">
    <listOfUnitDefinitions>
      <unitDefinition id="per_second">
        <listOfUnits>
          <unit kind="second" exponent="-1" scale="0" multiplier="1"/>
        </listOfUnits>
        <comp:listOfReplacedElements>
          <comp:replacedElement comp:idRef="per_second" comp:submodelRef="sm"/>
        </comp:listOfReplacedElements>
      </unitDefinition>
    </listOfUnitDefinitions>
    <listOfCompartments>
      <compartment metaid="meta_c" id="c" spatialDimensions="3" size="1"
                   constant="true">
        <comp:replacedBy comp:idRef="c" comp:submodelRef="sm"/>
      </compartment>
    </listOfCompartments>
    <listOfParameters>
      <parameter id="ctime" value="1" constant="true"/>
      <parameter id="cextent" value="1" constant="true"/>
    </listOfParameters>
    <comp:listOfSubmodels>
      <comp:submodel comp:id="sm" comp:modelRef="sub"
                     comp:timeConversionFactor="ctime"
                     comp:extentConversionFactor="cextent"/>
    </comp:listOfSubmodels>
    <comp:listOfPorts>
      <comp:port comp:id="unit_port" comp:unitRef="per_second"/>
      <comp:port comp:id="meta_port" comp:metaIdRef="meta_c"/>
    </comp:listOfPorts>
  </model>
  <comp:listOfModelDefinitions>
    <comp:modelDefinition id="sub">
      <listOfCompartments>
        <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
      </listOfCompartments>
    </comp:modelDefinition>
  </comp:listOfModelDefinitions>
</sbml>"""

SYNTHETIC_DISTRIB_SBML = f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:distrib="http://www.sbml.org/sbml/level3/version1/distrib/version1"
      level="3" version="1" distrib:required="true">
  <model id="unc">
    <listOfParameters>
      <parameter id="p1" value="1" constant="true">
        <distrib:listOfUncertainties>
          <distrib:uncertainty>
            <distrib:uncertParameter distrib:type="mean">
              {_mathml("2 * p2")}
            </distrib:uncertParameter>
          </distrib:uncertainty>
        </distrib:listOfUncertainties>
      </parameter>
      <parameter id="p2" value="2" constant="true"/>
    </listOfParameters>
  </model>
</sbml>"""


@pytest.fixture(scope="module")
def synthetic_fbc() -> Report:
    """The report of the synthetic core and fbc model."""
    return SBMLDocumentInfo.from_sbml(SYNTHETIC_FBC_SBML)


@pytest.fixture(scope="module")
def synthetic_comp() -> Report:
    """The report of the synthetic comp model."""
    return SBMLDocumentInfo.from_sbml(SYNTHETIC_COMP_SBML)


def test_bound_variables_are_no_math_edges(synthetic_fbc: Report) -> None:
    """A bound variable of a lambda does not link to the parameter of its name."""
    fd = synthetic_fbc.models[0].list_of_function_definitions[0]
    assert _edges(synthetic_fbc, source=fd.pk) == {
        (fd.pk, "synth/Parameter:k", "math"),
    }


def test_associated_species_edge(synthetic_fbc: Report) -> None:
    """A gene product links to its associated species."""
    gp = synthetic_fbc.models[0].list_of_gene_products[0]
    assert _edges(synthetic_fbc, source=gp.pk) == {
        (gp.pk, "synth/Species:s", "associatedSpecies"),
    }


def test_symbol_edge(synthetic_fbc: Report) -> None:
    """An initial assignment links to its symbol and to the symbols of its math."""
    ia = synthetic_fbc.models[0].list_of_initial_assignments[0]
    assert _edges(synthetic_fbc, source=ia.pk) == {
        (ia.pk, "synth/Species:s", "symbol"),
        (ia.pk, "synth/Parameter:k", "math"),
    }


def test_conversion_factor_edges(synthetic_fbc: Report) -> None:
    """The model and a species link to their conversion factor parameter."""
    model = synthetic_fbc.models[0]
    assert _edges(synthetic_fbc, kind=EdgeKind.CONVERSION_FACTOR) == {
        (model.pk, "synth/Parameter:cf", "conversionFactor"),
        ("synth/Species:s", "synth/Parameter:cf_s", "conversionFactor"),
    }


def test_local_parameter_shadows_global_parameter(synthetic_fbc: Report) -> None:
    """The math of a kinetic law resolves its symbols against the local parameters."""
    klaw = synthetic_fbc.models[0].list_of_reactions[0].kinetic_law
    assert klaw is not None
    assert _edges(synthetic_fbc, source=klaw.pk) == {
        (klaw.pk, "synth/LocalParameter:r.kineticLaw.k", "math"),
        (klaw.pk, "synth/Species:s", "math"),
    }


def test_replaced_by_edge(synthetic_comp: Report) -> None:
    """An element replaced by an element of a submodel links to that element."""
    replaced_by = "top/ReplacedBy:c.replacedBy"
    assert _edges(synthetic_comp, source=replaced_by) == {
        (replaced_by, "top/Submodel:sm", "replacedBy"),
        (replaced_by, "sub/Compartment:c", "replacedBy"),
    }
    assert ("top/Compartment:c", replaced_by, "replacedBy") in _edges(synthetic_comp)


def test_replacement_edges_of_every_element(synthetic_comp: Report) -> None:
    """Replacements are edges for every element type, not only the core lists."""
    replaced = "top/ReplacedElement:per_second.replacedElement.0"
    assert (
        "top/UnitDefinition:per_second",
        replaced,
        "replacedElement",
    ) in _edges(synthetic_comp)
    assert (replaced, "top/Submodel:sm", "replacedElement") in _edges(synthetic_comp)


def test_port_unit_ref_edge(synthetic_comp: Report) -> None:
    """A port referencing a unit definition is a port edge, not a units edge."""
    assert _edges(synthetic_comp, source="top/Port:unit_port") == {
        ("top/Port:unit_port", "top/UnitDefinition:per_second", "port"),
    }


def test_port_meta_id_ref_edge(synthetic_comp: Report) -> None:
    """A port referencing an element by metaId links to the element."""
    assert _edges(synthetic_comp, source="top/Port:meta_port") == {
        ("top/Port:meta_port", "top/Compartment:c", "port"),
    }


def test_submodel_edge_to_model_definition(synthetic_comp: Report) -> None:
    """A submodel links to the model definition it instantiates."""
    definition = synthetic_comp.models[1]
    assert _edges(synthetic_comp, kind=EdgeKind.MODEL_REF) == {
        ("top/Submodel:sm", definition.pk, "modelRef"),
    }


def test_submodel_conversion_factor_edges(synthetic_comp: Report) -> None:
    """A submodel links to the time and extent conversion factors of its model."""
    assert _edges(
        synthetic_comp, source="top/Submodel:sm", kind=EdgeKind.CONVERSION_FACTOR
    ) == {
        ("top/Submodel:sm", "top/Parameter:ctime", "conversionFactor"),
        ("top/Submodel:sm", "top/Parameter:cextent", "conversionFactor"),
    }


def test_uncertainty_math_edge() -> None:
    """The math of an uncertainty links to the elements it references."""
    report = SBMLDocumentInfo.from_sbml(SYNTHETIC_DISTRIB_SBML)
    uncertainty = report.models[0].list_of_parameters[0].uncertainties[0]
    assert uncertainty.pk in report.link_graph.nodes
    assert _edges(report, source=uncertainty.pk) == {
        (uncertainty.pk, "unc/Parameter:p2", "math"),
    }


def test_level_2_local_parameter_edges(
    level2_biomodel: Report, caplog: pytest.LogCaptureFixture
) -> None:
    """The math of a Level 2 kinetic law links to the parameters of that law."""
    reaction = next(
        r for r in level2_biomodel.models[0].list_of_reactions if r.id == "reaction1"
    )
    kinetic_law = reaction.kinetic_law
    assert kinetic_law is not None
    (local_parameter,) = kinetic_law.list_of_local_parameters
    assert local_parameter.id == "vi"
    assert (kinetic_law.pk, local_parameter.pk, "math") in _edges(level2_biomodel)
    # the parameter is in the namespace of its kinetic law, not of the model
    with caplog.at_level(logging.WARNING, logger="sbml4humans.links"):
        graph = build_link_graph(level2_biomodel, {kinetic_law.pk: {"vi"}})
    assert caplog.text == ""
    assert (
        Edge(source=kinetic_law.pk, target=local_parameter.pk, kind=EdgeKind.MATH)
        in graph.edges
    )


SYNTHETIC_STOICHIOMETRY_SBML = f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model id="var">
    <listOfCompartments>
      <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="S1" compartment="c" initialConcentration="1"
               hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="S2" compartment="c" initialConcentration="0"
               hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfParameters>
      <parameter id="p" value="2" constant="true"/>
    </listOfParameters>
    <listOfRules>
      <assignmentRule id="rule_sr1" variable="sr1">{_mathml("p")}</assignmentRule>
    </listOfRules>
    <listOfReactions>
      <reaction id="R1" reversible="false">
        <listOfReactants>
          <speciesReference id="sr1" species="S1" constant="false"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="S2" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <kineticLaw>{_mathml("sr1 * S1")}</kineticLaw>
      </reaction>
    </listOfReactions>
  </model>
</sbml>"""


def test_rule_of_a_species_reference_does_not_shadow_it() -> None:
    """A rule setting a stoichiometry links to the species reference.

    The variable of the rule is the id of a species reference, which used to
    be shadowed in the index by the rule itself, because libsbml reports the
    variable as the id of the rule (core §4.9.1, §4.11.3).
    """
    report = SBMLDocumentInfo.from_sbml(SYNTHETIC_STOICHIOMETRY_SBML)
    model = report.models[0]
    rule = model.list_of_rules[0]
    species_reference = model.list_of_reactions[0].list_of_reactants[0]
    kinetic_law = model.list_of_reactions[0].kinetic_law
    assert kinetic_law is not None
    assert rule.pk == "var/AssignmentRule:rule_sr1"
    assert species_reference.pk == "var/SpeciesReference:sr1"
    assert not [e for e in report.link_graph.edges if e.source == e.target]
    assert (rule.pk, species_reference.pk, "variable") in _edges(report)
    assert (kinetic_law.pk, species_reference.pk, "math") in _edges(report)


def test_math_edges_start_at_the_trigger_and_the_delay() -> None:
    """Every math of an event is read by the object which carries it.

    The trigger, the priority and the delay each hold their own math (core
    §4.12.2 to §4.12.4), so a reader can tell whether an element is read by the
    condition or by the delay expression.
    """
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "constraint_event.xml")
    (event,) = report.models[0].list_of_events
    assert event.trigger is not None
    assert event.delay is not None
    assert _edges(report, source=event.pk, kind=EdgeKind.MATH) == set()
    assert _edges(report, source=event.trigger.pk) == {
        (event.trigger.pk, "constraint_event/Parameter:t_dose", "math")
    }
    assert _edges(report, source=event.delay.pk) == {
        (event.delay.pk, "constraint_event/Parameter:t_delay", "math")
    }
    nodes = report.link_graph.nodes
    assert event.priority is not None
    for pk in (event.trigger.pk, event.priority.pk, event.delay.pk):
        assert pk in nodes


def test_an_event_names_its_trigger_its_priority_and_its_delay() -> None:
    """The event is in the graph over the three objects which hold its math.

    An event carries no reference of its own: its math belongs to its trigger,
    its priority and its delay (core §4.12.1), so without the three links the
    event would be a node without an edge and the links of the inspector would
    be empty.
    """
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "constraint_event.xml")
    (event,) = report.models[0].list_of_events
    assert event.trigger is not None
    assert event.priority is not None
    assert event.delay is not None
    assert _edges(report, source=event.pk) == {
        (event.pk, event.trigger.pk, "trigger"),
        (event.pk, event.priority.pk, "priority"),
        (event.pk, event.delay.pk, "delay"),
    }


# -------------------------------------------------------------------------------------
# the edges of the replacements and the deletions of comp
# -------------------------------------------------------------------------------------
def test_submodel_names_its_deletions(comp_deletion: Report) -> None:
    """A submodel lists its deletions and every deletion names what it removes.

    The reference of a deletion is resolved in the model the submodel
    instantiates (comp §3.5.3), by port, id, unit id or meta id.
    """
    m = "comp_deletion"
    assert _edges(comp_deletion, source=f"{m}/Submodel:cell1") == {
        (f"{m}/Submodel:cell1", f"{m}/Deletion:del_k", "deletion"),
        (f"{m}/Submodel:cell1", f"{m}/Deletion:del_sink", "deletion"),
        (f"{m}/Submodel:cell1", "cell/Model:cell", "modelRef"),
    }
    assert _edges(comp_deletion, source=f"{m}/Deletion:del_k") == {
        (f"{m}/Deletion:del_k", "cell/Parameter:k", "deletion"),
    }
    assert _edges(comp_deletion, source=f"{m}/Deletion:del_sink") == {
        (f"{m}/Deletion:del_sink", "cell/Reaction:sink", "deletion"),
    }


def test_replacement_ends_at_the_replaced_element(comp_deletion: Report) -> None:
    """A replacement links to the element of the submodel it names (comp §3.6.2).

    The element lists its replacements, and every replacement names the
    submodel and the element inside it, so that a reader of the species reaches
    the species it replaces instead of the submodel around it.
    """
    m = "comp_deletion"
    replaced = f"{m}/ReplacedElement:meta_glc_cell1"
    assert (f"{m}/Species:glc", replaced, "replacedElement") in _edges(comp_deletion)
    assert _edges(comp_deletion, source=replaced) == {
        (replaced, f"{m}/Submodel:cell1", "replacedElement"),
        (replaced, "cell/Species:glc", "replacedElement"),
        (replaced, f"{m}/Parameter:f_amount", "conversionFactor"),
    }


def test_replacement_follows_a_nested_reference(comp_deletion: Report) -> None:
    """A replacement reaching into a submodel of a submodel ends at its element.

    The chain of comp §3.7.2 names the submodel of the submodel first and the
    element of its model below that.
    """
    replaced = "comp_deletion/ReplacedElement:meta_medium_tissue"
    assert _edges(comp_deletion, source=replaced) == {
        (replaced, "comp_deletion/Submodel:tissue1", "replacedElement"),
        (replaced, "cell/Compartment:c", "replacedElement"),
    }


def test_replacement_of_a_deleted_element(comp_deletion: Report) -> None:
    """A replacement scoped to a deletion names the deletion (comp §3.6.2)."""
    m = "comp_deletion"
    replaced = f"{m}/ReplacedElement:meta_k_total_cell1"
    assert _edges(comp_deletion, source=replaced) == {
        (replaced, f"{m}/Deletion:del_k", "deletion"),
        (replaced, f"{m}/Submodel:cell1", "replacedElement"),
    }


def test_replaced_by_ends_at_the_replacing_element(comp_deletion: Report) -> None:
    """The element which replaces an element is linked (comp §3.6.4)."""
    m = "comp_deletion"
    replaced_by = f"{m}/ReplacedBy:meta_Vmax_shared"
    assert (f"{m}/Parameter:Vmax_shared", replaced_by, "replacedBy") in _edges(
        comp_deletion
    )
    assert _edges(comp_deletion, source=replaced_by) == {
        (replaced_by, f"{m}/Submodel:cell2", "replacedBy"),
        (replaced_by, "cell/Parameter:Vmax", "replacedBy"),
    }


def test_port_follows_its_reference(comp_deletion: Report) -> None:
    """A port links to the element it names, whichever of the four ways it uses."""
    m = "comp_deletion"
    assert _edges(comp_deletion, kind=EdgeKind.PORT) == {
        (f"{m}/Port:medium_port", f"{m}/Compartment:medium", "port"),
        (f"{m}/Port:per_min_port", f"{m}/UnitDefinition:per_min", "port"),
        (
            f"{m}/Port:glc_amount_rule_port",
            f"{m}/AssignmentRule:glc_amount",
            "port",
        ),
        ("cell/Port:cell_port", "cell/Compartment:c", "port"),
        ("cell/Port:glc_port", "cell/Species:glc", "port"),
        ("cell/Port:Vmax_port", "cell/Parameter:Vmax", "port"),
    }


def test_deletion_in_an_external_model_names_no_element(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A deletion of an external submodel keeps the name of what it removes.

    The submodel `unit_library` instantiates an external model definition, and
    the document behind it is not part of the report, so the deletion has no
    element to link and the report says why.
    """
    with caplog.at_level(logging.WARNING, logger="sbml4humans.links"):
        report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "comp_deletion.xml")
    m = "comp_deletion"
    deletion = f"{m}/Deletion:del_external_unit"
    assert (f"{m}/Submodel:unit_library", deletion, "deletion") in _edges(report)
    assert _edges(report, source=deletion) == set()
    assert "is not part of the report" in caplog.text


def test_replacement_into_an_external_model_ends_at_the_submodel(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A reference the report cannot follow ends at the submodel, and says why.

    The submodel of `icg_body` instantiates an external model definition, whose
    document the report does not read, so the element the replacement names is
    not part of the report.
    """
    with caplog.at_level(logging.WARNING, logger="sbml4humans.links"):
        report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    m = "icg_body"
    replaced = f"{m}/ReplacedElement:Cli_plasma_icg_RE"
    assert (replaced, f"{m}/Submodel:LI", "replacedElement") in _edges(report)
    assert "not part of the report" in caplog.text


# -------------------------------------------------------------------------------------
# the identifiers of a port are a namespace of their own
# -------------------------------------------------------------------------------------
PORT_NAMESPACE_SBML = f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core"
      xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1"
      level="3" version="1" comp:required="true">
  <model id="ports">
    <listOfParameters>
      <parameter id="k" value="1" constant="true"/>
      <parameter id="v" value="0" constant="false"/>
    </listOfParameters>
    <listOfRules>
      <assignmentRule variable="v">{_mathml("Vmax")}</assignmentRule>
    </listOfRules>
    <comp:listOfPorts>
      <comp:port comp:id="Vmax" comp:idRef="k"/>
    </comp:listOfPorts>
  </model>
</sbml>"""


def test_port_id_is_no_element_of_the_sid_namespace() -> None:
    """A port identifier is a namespace of its own (comp §3.4.3).

    A port identifier may be the identifier of an element of the model without
    naming it, so a symbol of a formula never resolves to a port: `Vmax` above
    is the identifier of a port and of nothing else, and the formula which uses
    it names nothing.
    """
    report = SBMLDocumentInfo.from_sbml(PORT_NAMESPACE_SBML)
    assert _edges(report, source="ports/AssignmentRule:v") == {
        ("ports/AssignmentRule:v", "ports/Parameter:v", "variable"),
    }
    assert _edges(report, source="ports/Port:Vmax") == {
        ("ports/Port:Vmax", "ports/Parameter:k", "port"),
    }
    assert "ports/Port:Vmax" in report.link_graph.nodes


def test_active_objective_edge() -> None:
    """The model names the objective it declares as the active one."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    m = "fbc_constraints_v3"
    assert _edges(report, kind=EdgeKind.ACTIVE_OBJECTIVE) == {
        (f"{m}/Model:{m}", f"{m}/Objective:growth_max", "activeObjective"),
    }


def test_flux_objective_edges_start_at_the_flux_objective() -> None:
    """The objective names its flux objectives and each of them names its reactions."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    m = "fbc_constraints_v3"
    quadratic = f"{m}/FluxObjective:fo_uptake"
    assert (f"{m}/Objective:uptake_min", quadratic, "fluxObjective") in _edges(report)
    assert _edges(report, source=quadratic) == {
        (quadratic, f"{m}/Reaction:v1", "fluxObjective"),
        (quadratic, f"{m}/Reaction:v2", "fluxObjective"),
    }


def test_flux_bound_edge_of_a_version_1_model() -> None:
    """A flux bound of a Version 1 model names the reaction it constrains."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_bounds_v1.xml")
    m = "fbc_bounds_v1"
    assert _edges(report, kind=EdgeKind.FLUX_BOUND) == {
        (f"{m}/FluxBound:v1_lb", f"{m}/Reaction:v1", "fluxBound"),
        (f"{m}/FluxBound:v1_ub", f"{m}/Reaction:v1", "fluxBound"),
        (f"{m}/FluxBound:EX_glc_fixed", f"{m}/Reaction:EX_glc", "fluxBound"),
    }


def test_user_defined_constraint_edges() -> None:
    """A constraint names its bounds and its components, a component its variables."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_constraints_v3.xml")
    m = "fbc_constraints_v3"
    constraint = f"{m}/UserDefinedConstraint:ratio"
    component = f"{m}/UserDefinedConstraintComponent:ratio_v1"
    assert _edges(report, source=constraint) == {
        (constraint, f"{m}/Parameter:ratio_lb", "fluxBound"),
        (constraint, f"{m}/Parameter:ratio_ub", "fluxBound"),
        (constraint, component, "constraintComponent"),
        (
            constraint,
            f"{m}/UserDefinedConstraintComponent:ratio_v2",
            "constraintComponent",
        ),
    }
    assert _edges(report, source=component) == {
        (component, f"{m}/Reaction:v1", "variable"),
        (component, f"{m}/Parameter:c_two", "coefficient"),
    }
    quadratic = f"{m}/UserDefinedConstraintComponent:budget_v2"
    assert (quadratic, f"{m}/Parameter:maintenance", "variable") in _edges(report)
