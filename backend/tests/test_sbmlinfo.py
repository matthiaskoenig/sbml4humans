"""Tests of the report information of a document."""

import libsbml
import pytest

from sbml4humans.resources import EXAMPLES_DIR, REPRESSILATOR_SBML
from sbml4humans.sbml import read_sbml
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.units import udef_to_string


REACTION_SBML = EXAMPLES_DIR / "reaction.xml"


def test_info_for_repressilator() -> None:
    """The report information is created for a model."""
    info = SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)
    assert info.info["doc"]
    assert info.info["model"]["reactions"]


def test_info_for_variable_stoichiometry() -> None:
    """Reactions with variable (NaN) stoichiometry get an equation."""
    info = SBMLDocumentInfo.from_sbml(REACTION_SBML)
    equations = {r["id"]: r["equation"] for r in info.info["model"]["reactions"]}
    assert equations["v1"] == "x &#10142; y"
    assert equations["v2"] == "x &#10142; 2.0 y"
    # stoichiometry set by rules via the species reference id
    assert equations["v3"] == "f1 x &#10142; f2 y"
    assert equations["v4"] == "v4_x x &#10142; v4_y y"


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
