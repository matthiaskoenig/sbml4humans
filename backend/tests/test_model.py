"""Tests of the report data model."""

from sbml4humans.model import CVTerm, Math, SBase


def test_json_uses_camel_case() -> None:
    """Fields are snake_case in python and camelCase in JSON."""
    sbase = SBase(pk="m/SBase:x", sbml_type="SBase", id="x", meta_id="meta_x")
    data = sbase.model_dump(mode="json", by_alias=True)
    assert data["metaId"] == "meta_x"
    assert data["sbmlType"] == "SBase"
    assert "meta_id" not in data


def test_validation_accepts_both_spellings() -> None:
    """JSON is validated back from the aliases and from the field names."""
    from_alias = SBase.model_validate({"pk": "p", "sbmlType": "SBase", "metaId": "m"})
    from_name = SBase.model_validate({"pk": "p", "sbml_type": "SBase", "meta_id": "m"})
    assert from_alias == from_name


def test_sbase_defaults() -> None:
    """Optional attributes default to None and the lists to empty."""
    sbase = SBase(pk="p", sbml_type="SBase")
    assert sbase.id is None
    assert sbase.cvterms == []
    assert sbase.history is None
    assert sbase.comp is None
    assert sbase.uncertainties == []


def test_math_and_cvterm() -> None:
    """Value types hold their fields."""
    math = Math(latex=r"\mathit{x}", formula="x")
    assert math.formula == "x"
    cvterm = CVTerm(
        qualifier="BQB_IS", resources=["https://identifiers.org/chebi/CHEBI:1"]
    )
    assert (
        cvterm.model_dump(mode="json", by_alias=True)["resources"] == cvterm.resources
    )
