"""Tests of the report information of a document."""

import libsbml
import pytest

from sbml4humans.model import Model, Report
from sbml4humans.resources import EXAMPLES_DIR, REPRESSILATOR_SBML
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
    assert reaction.equation == "X &#10142; "
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
    assert equations["v1"] == "x &#10142; y"
    assert equations["v2"] == "x &#10142; 2.0 y"
    assert equations["v3"] == "f1 x &#10142; f2 y"
    assert equations["v4"] == "v4_x x &#10142; v4_y y"


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
