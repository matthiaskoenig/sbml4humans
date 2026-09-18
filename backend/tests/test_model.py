"""Tests of the report data model."""

import json
from pathlib import Path

import pytest

from sbml4humans.model import (
    AlgebraicRule,
    AssignmentRule,
    Compartment,
    CVTerm,
    Edge,
    EdgeKind,
    FluxBound,
    LinkGraph,
    Math,
    Model,
    Node,
    Parameter,
    RateRule,
    Report,
    SBase,
    SBMLDocument,
    Species,
)
from sbml4humans.resources import API_EXAMPLES_MODEL
from sbml4humans.sbmlinfo import SBMLDocumentInfo


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


def test_an_infinite_value_is_carried_as_the_constant_it_is() -> None:
    """JSON has no literal for an infinite value, the report writes the constant.

    `inf` used to serialise as `null`, so the upper bound `INF` of a reaction,
    the value of an unbounded parameter and an attribute the file does not set
    at all read as the same dash in the report.
    """
    upper = Parameter(pk="m/Parameter:ub", id="ub", value=float("inf"))
    lower = Parameter(pk="m/Parameter:lb", id="lb", value=float("-inf"))
    unset = Parameter(pk="m/Parameter:p", id="p")
    dumped = [
        json.loads(p.model_dump_json(by_alias=True))["value"]
        for p in (upper, lower, unset)
    ]
    assert dumped == ["Infinity", "-Infinity", None]


def test_a_value_which_is_not_a_number_is_carried_as_well() -> None:
    """A NaN is a value of a double like an infinite one, and is carried like one."""
    species = Species(
        pk="m/Species:s", id="s", compartment="c", initial_amount=float("nan")
    )
    dumped = json.loads(species.model_dump_json(by_alias=True))
    assert dumped["initialAmount"] == "NaN"


def test_every_double_of_the_report_carries_them() -> None:
    """The decision is one of the whole report, not of one class of it."""
    bound = FluxBound(pk="m/FluxBound:b", id="b", value=float("inf"))
    compartment = Compartment(pk="m/Compartment:c", id="c", size=float("inf"))
    assert json.loads(bound.model_dump_json(by_alias=True))["value"] == "Infinity"
    assert json.loads(compartment.model_dump_json(by_alias=True))["size"] == "Infinity"


def test_an_infinite_value_validates_back() -> None:
    """The constants are read back into the doubles they stand for."""
    parameter = Parameter.model_validate({"pk": "m/Parameter:ub", "value": "Infinity"})
    assert parameter.value == float("inf")


def _model() -> Model:
    """A model with one compartment and species."""
    return Model(
        pk="m/Model:m",
        id="m",
        kind="model",
        list_of_compartments=[Compartment(pk="m/Compartment:c", id="c", size=1.0)],
        list_of_species=[Species(pk="m/Species:s", id="s", compartment="c")],
        list_of_rules=[
            AssignmentRule(pk="m/AssignmentRule:r1", variable="s", math=None),
            RateRule(pk="m/RateRule:r2", variable="c", math=None),
            AlgebraicRule(pk="m/AlgebraicRule:r3", math=None),
        ],
    )


def test_sbml_type_is_fixed_per_class() -> None:
    """Every object carries its sbml type as literal."""
    species = Species(pk="m/Species:s", id="s", compartment="c")
    assert species.sbml_type == "Species"
    assert species.model_dump(mode="json", by_alias=True)["sbmlType"] == "Species"


def test_rules_are_discriminated_by_sbml_type() -> None:
    """The rules of a model validate back into their classes."""
    data = _model().model_dump(mode="json", by_alias=True)
    model = Model.model_validate(data)
    assert [type(r).__name__ for r in model.list_of_rules] == [
        "AssignmentRule",
        "RateRule",
        "AlgebraicRule",
    ]


def test_report_round_trip() -> None:
    """A report dumps to JSON and validates back unchanged."""
    graph = LinkGraph(
        nodes={
            "m/Species:s": Node(
                pk="m/Species:s", sbml_type="Species", id="s", model="m/Model:m"
            ),
            "m/Compartment:c": Node(
                pk="m/Compartment:c", sbml_type="Compartment", id="c", model="m/Model:m"
            ),
        },
        edges=[
            Edge(
                source="m/Species:s",
                target="m/Compartment:c",
                kind=EdgeKind.COMPARTMENT,
            )
        ],
    )
    report = Report(
        document=SBMLDocument(pk="document/SBMLDocument:document", level=3, version=2),
        models=[_model()],
        link_graph=graph,
    )
    data = report.model_dump(mode="json", by_alias=True)
    assert data["linkGraph"]["edges"][0]["kind"] == "compartment"
    assert data["models"][0]["listOfSpecies"][0]["compartment"] == "c"
    assert Report.model_validate(data) == report


@pytest.mark.parametrize("path", API_EXAMPLES_MODEL, ids=lambda path: path.name)
def test_examples_round_trip(path: Path) -> None:
    """Every example builds a report which survives the JSON round trip."""
    report = SBMLDocumentInfo.from_sbml(path)
    data = report.model_dump(mode="json", by_alias=True)
    assert Report.model_validate(data) == report
    nodes = report.link_graph.nodes
    pks = [n.pk for n in nodes.values()]
    assert len(pks) == len(set(pks))
    for edge in report.link_graph.edges:
        assert edge.source in nodes and edge.target in nodes
