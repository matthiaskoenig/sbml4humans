"""Tests of the report data model."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from sbml4humans.model import (
    AlgebraicRule,
    AssignmentRule,
    Compartment,
    CVTerm,
    Edge,
    EdgeKind,
    ExternalModelDefinition,
    ExternalModelResolution,
    LinkGraph,
    ListOf,
    Math,
    Model,
    Node,
    Parameter,
    RateRule,
    Report,
    ReportResponse,
    ResolutionStatus,
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
    assert sbase.lists == []


def test_a_list_is_an_sbase_with_the_lists_of_one() -> None:
    """A list carries the fields of an `SBase`, its element name and its size.

    One type stands for every `ListOf` class of SBML, and the JSON names the
    lists of an element and the fields of a list in camelCase like the rest.
    """
    list_of = ListOf(
        pk="m/ListOf:metabolites",
        id="metabolites",
        meta_id="meta_species",
        element="listOfSpecies",
        size=2,
    )
    assert list_of.sbml_type == "ListOf"
    assert isinstance(list_of, SBase)
    model = Model(pk="m/Model:m", id="m", lists=[list_of])
    data = model.model_dump(mode="json", by_alias=True)
    (dumped,) = data["lists"]
    assert dumped["sbmlType"] == "ListOf"
    assert dumped["metaId"] == "meta_species"
    assert (dumped["element"], dumped["size"]) == ("listOfSpecies", 2)
    assert dumped["lists"] == []
    assert Model.model_validate(data) == model


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


def _number_properties(schema: object, path: str = "") -> Iterator[tuple[str, object]]:
    """Every property of a JSON schema which accepts a number, with its path."""
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                for name, prop in value.items():
                    if '"number"' in json.dumps(prop):
                        yield f"{path}.{name}", prop
            yield from _number_properties(value, f"{path}/{key}")
    elif isinstance(schema, list):
        for item in schema:
            yield from _number_properties(item, path)


def test_every_double_of_the_report_carries_them() -> None:
    """Every double of the schema says that it may be one of the three constants.

    The frontend types are generated from the schema, and a renderer only
    reads the constants where the type of a field names them: a float of the
    model which is not a `Double` would send "Infinity" to a field typed as a
    number alone.
    """
    schema = ReportResponse.model_json_schema(by_alias=True)
    properties = dict(_number_properties(schema))
    assert properties
    constants = [{"const": "Infinity"}, {"const": "-Infinity"}, {"const": "NaN"}]
    missing = [
        path
        for path, prop in properties.items()
        if not all(json.dumps(c) in json.dumps(prop) for c in constants)
    ]
    assert missing == []


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


def test_an_edge_stays_in_its_entry_unless_it_names_another() -> None:
    """The entry of the target is part of the JSON and unset for a local edge."""
    local = Edge(source="m/Species:a", target="m/Compartment:c", kind=EdgeKind.UNITS)
    assert local.model_dump(mode="json", by_alias=True)["targetEntry"] is None
    across = Edge(
        source="m/ReplacedElement:a.replacedElement.0",
        target="sub/Species:a",
        kind=EdgeKind.REPLACED_ELEMENT,
        target_entry="./models/sub.xml",
    )
    assert across.model_dump(mode="json", by_alias=True)["targetEntry"] == (
        "./models/sub.xml"
    )
    # the entry is part of the identity of an edge: two entries may hold one pk
    assert across != Edge(source=across.source, target=across.target, kind=across.kind)


def test_an_external_model_definition_carries_its_resolution() -> None:
    """The resolution is unresolved until the entries of the archive are known."""
    emd = ExternalModelDefinition(
        pk="document/ExternalModelDefinition:emd", id="emd", source="sub.xml"
    )
    assert emd.resolution == ExternalModelResolution(status=ResolutionStatus.NOT_FOUND)
    emd.resolution = ExternalModelResolution(
        status=ResolutionStatus.RESOLVED,
        entry="./sub.xml",
        model="sub/Model:sub",
        md5_matches=True,
    )
    data = emd.model_dump(mode="json", by_alias=True)["resolution"]
    assert data == {
        "status": "resolved",
        "entry": "./sub.xml",
        "model": "sub/Model:sub",
        "md5Matches": True,
    }
    assert {status.value for status in ResolutionStatus} == {
        "resolved",
        "remoteSource",
        "notFound",
        "notSbml",
        "modelNotFound",
        "circular",
    }


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
