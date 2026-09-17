"""Tests of the report information of a document."""

import json

import libsbml
import pytest

from sbml4humans.model import Model, Report
from sbml4humans.resources import (
    COMP_ICG_BODY,
    EXAMPLES_DIR,
    FBC_ECOLI_CORE_SBML,
    REPRESSILATOR_SBML,
)
from sbml4humans.sbml import read_sbml
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.units import udef_to_string


@pytest.fixture(scope="module")
def repressilator() -> Report:
    """The report of the repressilator."""
    return SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)


def test_document(repressilator: Report) -> None:
    """The document carries level, version and its pk."""
    doc = repressilator.document
    assert doc.pk == "document/SBMLDocument:document"
    assert (doc.level, doc.version) == (2, 3)
    assert doc.xml is None


def test_model_and_lists(repressilator: Report) -> None:
    """The main model has the lists of its elements."""
    assert len(repressilator.models) == 1
    model: Model = repressilator.models[0]
    assert model.kind == "model"
    assert model.pk == "BIOMD0000000012/Model:BIOMD0000000012"
    assert [c.id for c in model.list_of_compartments] == ["cell"]
    assert [s.id for s in model.list_of_species] == ["PX", "PY", "PZ", "X", "Y", "Z"]
    assert len(model.list_of_reactions) == 12
    assert len(model.list_of_rules) == 9
    assert [u.id for u in model.list_of_unit_definitions] == [
        "volume",
        "substance",
        "time",
    ]


def test_pks_are_scoped_by_model(repressilator: Report) -> None:
    """Element pks carry the model id, the type and the id."""
    species = repressilator.models[0].list_of_species[0]
    assert species.pk == "BIOMD0000000012/Species:PX"
    assert species.compartment == "cell"


def test_reaction(repressilator: Report) -> None:
    """A reaction has its participants, equation and kinetic law."""
    reaction = repressilator.models[0].list_of_reactions[0]
    assert reaction.id == "Reaction1"
    assert [r.species for r in reaction.list_of_reactants] == ["X"]
    assert reaction.list_of_products == []
    assert reaction.equation == "X ➞ "
    assert reaction.kinetic_law is not None
    assert reaction.kinetic_law.math is not None
    assert reaction.kinetic_law.math.formula == "kd_mRNA * X"
    assert (
        reaction.list_of_reactants[0].pk == "BIOMD0000000012/SpeciesReference:_420973"
    )


def test_math_symbols_are_collected(repressilator: Report) -> None:
    """The symbols of every math are collected by the pk of its owner."""
    info = SBMLDocumentInfo(libsbml.readSBMLFromFile(str(REPRESSILATOR_SBML)))
    info.build()
    reaction = info.report.models[0].list_of_reactions[0]
    assert reaction.kinetic_law is not None
    assert info.symbols[reaction.kinetic_law.pk] == {"kd_mRNA", "X"}


def test_variable_stoichiometry() -> None:
    """Reactions with variable (NaN) stoichiometry get an equation."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "reaction.xml")
    equations = {r.id: r.equation for r in report.models[0].list_of_reactions}
    assert equations["v1"] == "x ➞ y"
    assert equations["v2"] == "x ➞ 2.0 y"
    assert equations["v3"] == "f1 x ➞ f2 y"
    assert equations["v4"] == "v4_x x ➞ v4_y y"


def test_nan_values_become_none() -> None:
    """NaN attributes are not JSON and are reported as unset."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "reaction.xml")
    reaction = next(r for r in report.models[0].list_of_reactions if r.id == "v3")
    assert reaction.list_of_reactants[0].stoichiometry is None


@pytest.mark.parametrize(
    "stoichiometry, expected",
    [
        (1.0, "x"),
        (-1.0, "-x"),
        (2.0, "2.0 x"),
        (-2.5, "-2.5 x"),
        (0.0, "0.0 x"),
        (float("nan"), "sr x"),
    ],
)
def test_half_equation(stoichiometry: float, expected: str) -> None:
    """Half equations for the different stoichiometries."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setId("sr")
    sr.setSpecies("x")
    sr.setStoichiometry(stoichiometry)
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == expected


def test_half_equation_nan_without_id() -> None:
    """A variable stoichiometry without species reference id is marked."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setSpecies("x")
    sr.setStoichiometry(float("nan"))
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == "? x"


def test_document_without_model() -> None:
    """A document without model has no models."""
    report = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
        'level="3" version="2"/>'
    )
    assert report.models == []


def test_model_without_id_is_scoped_by_its_key() -> None:
    """A model without id uses its metaId as scope of the pks."""
    report = SBMLDocumentInfo.from_sbml(
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">'
        '<model metaid="meta_m"><listOfCompartments>'
        '<compartment id="c" constant="true"/>'
        "</listOfCompartments></model></sbml>"
    )
    model = report.models[0]
    assert model.pk == "meta_m/Model:meta_m"
    assert model.list_of_compartments[0].pk == "meta_m/Compartment:c"


def test_sbo_is_added_as_cvterm() -> None:
    """The SBO term of an element is reported as BQB_IS annotation."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "annotation.xml")
    model = report.models[0]
    annotated = [s for s in model.list_of_species if s.sbo]
    assert annotated
    species = annotated[0]
    assert any(
        cv.qualifier == "BQB_IS"
        and f"https://identifiers.org/{species.sbo}" in cv.resources
        for cv in species.cvterms
    )


def test_read_sbml_from_string_and_path() -> None:
    """A document is read from a path and from an SBML string."""
    doc = read_sbml(REPRESSILATOR_SBML)
    assert doc.getModel() is not None
    doc = read_sbml(REPRESSILATOR_SBML.read_text())
    assert doc.getModel() is not None


def test_read_sbml_invalid() -> None:
    """An unreadable source gives a document without model."""
    doc = read_sbml("not sbml")
    assert doc.getModel() is None
    assert doc.getNumErrors() > 0


@pytest.mark.parametrize(
    "definition, expected",
    [
        ("mmole/min", r"\frac{mmol}{min}"),
        ("meter^3", "m^3"),
        ("dimensionless", "-"),
    ],
)
def test_udef_to_string(definition: str, expected: str) -> None:
    """Unit definitions are rendered as latex."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    udef = libsbml.UnitDefinition(3, 2)
    udef.setId("u")
    for kind, exponent, scale, multiplier in _units(definition):
        unit = udef.createUnit()
        unit.setKind(kind)
        unit.setExponent(exponent)
        unit.setScale(scale)
        unit.setMultiplier(multiplier)
    model.addUnitDefinition(udef)
    assert udef_to_string(udef) == expected


def _units(definition: str) -> list[tuple[int, int, int, float]]:
    """Units of the test definitions as (kind, exponent, scale, multiplier)."""
    return {
        "mmole/min": [
            (libsbml.UNIT_KIND_MOLE, 1, -3, 1.0),
            (libsbml.UNIT_KIND_SECOND, -1, 0, 60.0),
        ],
        "meter^3": [(libsbml.UNIT_KIND_METRE, 3, 0, 1.0)],
        "dimensionless": [(libsbml.UNIT_KIND_DIMENSIONLESS, 1, 0, 1.0)],
    }[definition]


def test_comp_model_definitions() -> None:
    """Model definitions are further models of the report."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "model_definitions.xml")
    assert [(m.id, m.kind) for m in report.models] == [
        ("model_definitions", "model"),
        ("m1", "modelDefinition"),
    ]
    assert report.models[1].pk == "m1/Model:m1"
    assert report.models[1].list_of_species[0].pk.startswith("m1/Species:")


def test_comp_sbase_without_replacements() -> None:
    """An element of a comp document without replacements has no comp extension."""
    report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    model = report.models[0]
    assert model.list_of_submodels
    assert [c for c in model.list_of_compartments if c.comp is None]
    assert [s for s in model.list_of_species if s.comp is not None]


def test_comp_submodels_ports_and_replacements() -> None:
    """Submodels, ports, external model definitions and replacements are reported."""
    report = SBMLDocumentInfo.from_sbml(COMP_ICG_BODY)
    model = report.models[0]
    assert [(s.id, s.model_ref) for s in model.list_of_submodels] == [("LI", "liver")]
    assert [
        (e.id, e.source, e.model_ref) for e in report.external_model_definitions
    ] == [("liver", "icg_liver.xml", "icg_liver")]
    assert (
        report.external_model_definitions[0].pk
        == "document/ExternalModelDefinition:liver"
    )
    port = model.list_of_ports[0]
    assert (port.id, port.id_ref) == ("Vre_tissue_port", "Vre_tissue")
    species = next(s for s in model.list_of_species if s.id == "Cli_plasma_icg")
    assert species.comp is not None
    replaced = species.comp.replaced_elements[0]
    assert (replaced.submodel_ref, replaced.sbase_ref.port_ref) == (
        "LI",
        "icg_ext_port",
    )


def test_fractional_spatial_dimensions() -> None:
    """The spatial dimensions of an L3 compartment can be fractional."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("m")
    compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setSpatialDimensions(2.5)
    report = SBMLDocumentInfo.from_doc(doc)
    assert report.models[0].list_of_compartments[0].spatial_dimensions == 2.5


def test_spatial_dimensions_unset() -> None:
    """A compartment without spatial dimensions reports them as unset."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("m")
    model.createCompartment().setId("c")
    report = SBMLDocumentInfo.from_doc(doc)
    assert report.models[0].list_of_compartments[0].spatial_dimensions is None


def test_species_units_are_the_substance_units() -> None:
    """The units of a species are its substance units, rendered as latex."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "multiple_substance_units.xml")
    species = [s for s in report.models[0].list_of_species if s.substance_units]
    assert species
    assert all(s.units_latex for s in species)


def test_fbc() -> None:
    """Flux bounds, gene product associations, gene products and objectives are reported."""
    report = SBMLDocumentInfo.from_sbml(FBC_ECOLI_CORE_SBML)
    model = report.models[0]
    reaction = next(r for r in model.list_of_reactions if r.id == "R_PFK")
    assert reaction.fbc is not None
    assert reaction.fbc.lower_flux_bound == "cobra_0_bound"
    assert reaction.fbc.upper_flux_bound == "cobra_default_ub"
    assert reaction.fbc.gene_product_association == "(b3916 or b1723)"
    assert sorted(reaction.fbc.gene_products) == ["G_b1723", "G_b3916"]
    assert len(model.list_of_gene_products) == 137
    objective = model.list_of_objectives[0]
    assert objective.id == "obj"
    assert [(f.reaction, f.coefficient) for f in objective.list_of_flux_objectives] == [
        ("R_BIOMASS_Ecoli_core_w_GAM", 1.0)
    ]


def test_charge_zero_is_reported() -> None:
    """A charge of zero is a charge, not an unset attribute."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "fbc_mass_charge.xml")
    species = next(s for s in report.models[0].list_of_species if s.id == "glc")
    assert species.fbc is not None
    assert species.fbc.charge == 0


def test_flux_objective_without_coefficient() -> None:
    """A flux objective without coefficient reports None instead of NaN."""
    doc = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, 1, "fbc", 2))
    model = doc.createModel()
    model.setId("m")
    plugin: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    objective: libsbml.Objective = plugin.createObjective()
    objective.setId("obj")
    objective.setType("maximize")
    objective.createFluxObjective().setReaction("r")
    report = SBMLDocumentInfo.from_doc(doc)
    flux_objective = report.models[0].list_of_objectives[0].list_of_flux_objectives[0]
    assert flux_objective.coefficient is None
    assert "NaN" not in json.dumps(report.model_dump(mode="json", by_alias=True))


def test_distrib_uncertainties() -> None:
    """Uncertainties of the distrib package are reported with their parameters."""
    report = SBMLDocumentInfo.from_sbml(EXAMPLES_DIR / "distrib_uncertainties.xml")
    model = report.models[0]
    with_uncertainty = [
        e for e in model.list_of_parameters + model.list_of_species if e.uncertainties
    ]
    assert with_uncertainty
    uncertainty = with_uncertainty[0].uncertainties[0]
    assert uncertainty.sbml_type == "Uncertainty"
    assert uncertainty.uncert_parameters
    assert uncertainty.uncert_parameters[0].type is not None


def test_reactant_pks_are_unique_across_reactions() -> None:
    """Species references without ids of two reactions get distinct pks.

    Species references without an id are byte identical xml across reactions
    consuming the same species, so the digest fallback of the pk used to
    collide; the pk is now keyed by the reaction and the side instead.
    """
    sbml = (
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
        'level="3" version="2">'
        '<model id="m"><listOfCompartments>'
        '<compartment id="c" constant="true"/>'
        "</listOfCompartments><listOfSpecies>"
        '<species id="s" compartment="c" hasOnlySubstanceUnits="false" '
        'boundaryCondition="false" constant="false"/>'
        "</listOfSpecies><listOfReactions>"
        '<reaction id="r1" reversible="false"><listOfReactants>'
        '<speciesReference species="s" constant="true"/>'
        "</listOfReactants></reaction>"
        '<reaction id="r2" reversible="false"><listOfReactants>'
        '<speciesReference species="s" constant="true"/>'
        "</listOfReactants></reaction>"
        "</listOfReactions></model></sbml>"
    )
    report = SBMLDocumentInfo.from_sbml(sbml)
    reactant_pks = [
        r.list_of_reactants[0].pk for r in report.models[0].list_of_reactions
    ]
    assert reactant_pks == [
        "m/SpeciesReference:r1.reactant.s",
        "m/SpeciesReference:r2.reactant.s",
    ]
    assert len(reactant_pks) == len(set(reactant_pks))
