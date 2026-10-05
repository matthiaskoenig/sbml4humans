"""Tests of the JSON schema export."""

import json
from pathlib import Path

from sbml4humans.schema import SCHEMA_PATH, schema_json


def test_schema_describes_the_response() -> None:
    """The schema is the JSON schema of the report response."""
    schema = json.loads(schema_json())
    assert schema["title"] == "ReportResponse"
    assert set(schema["properties"]) == {"uid", "manifest", "reports"}
    assert "Species" in schema["$defs"]
    assert "listOfSpecies" in schema["$defs"]["Model"]["properties"]


def test_defs_are_titled_without_titled_properties() -> None:
    """Every `$defs` entry keeps its class name, no property is titled.

    Pydantic titles every property by default (`"title": "Sbmltype"`), which
    makes json-schema-to-typescript hoist every titled property into its own
    named type alias instead of reusing the `$defs` entry.
    """
    schema = json.loads(schema_json())
    defs = schema["$defs"]
    assert defs, "the schema has $defs entries"
    for name, entry in defs.items():
        assert "title" in entry, f"{name} has no title"
        for prop_name, prop_schema in entry.get("properties", {}).items():
            assert "title" not in prop_schema, (
                f"{name}.{prop_name} carries a property title"
            )


def test_a_double_may_be_an_infinite_value() -> None:
    """The schema says what the api sends, so the frontend types say it too.

    JSON has no literal for an infinite value or for one which is not a number,
    and the report writes the three constants of a double as strings.
    """
    schema = json.loads(schema_json())
    value = schema["$defs"]["Parameter"]["properties"]["value"]
    assert {"type": "number"} in value["anyOf"]
    assert {"const": "Infinity"} in value["anyOf"]
    assert {"const": "-Infinity"} in value["anyOf"]
    assert {"const": "NaN"} in value["anyOf"]
    assert {"type": "null"} in value["anyOf"]


def test_committed_schema_is_current() -> None:
    """The schema of the frontend equals the schema of the current model."""
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_json(), (
        "run `uv run python -m sbml4humans.schema` and commit the schema"
    )


def test_annotation_schema_is_current() -> None:
    """The committed schema of the annotation resource is the one the model generates."""
    from sbml4humans.schema import ANNOTATION_SCHEMA_PATH, annotation_schema_json

    assert (
        ANNOTATION_SCHEMA_PATH.read_text(encoding="utf-8") == annotation_schema_json()
    )


def test_validation_schema_is_current() -> None:
    """The committed schema of the validation is the one the model generates."""
    from sbml4humans.schema import VALIDATION_SCHEMA_PATH, validation_schema_json

    assert (
        VALIDATION_SCHEMA_PATH.read_text(encoding="utf-8") == validation_schema_json()
    )


def test_validation_schema_describes_the_response() -> None:
    """The schema of the validation is the one of its response."""
    from sbml4humans.schema import validation_schema_json

    schema = json.loads(validation_schema_json())
    assert schema["title"] == "ValidationResponse"
    assert set(schema["properties"]) == {"entries", "skipped"}
    entry = schema["$defs"]["EntryValidation"]
    reasons = ["expandedSize", "timeout", "memory", "busy"]
    assert {"enum": reasons, "type": "string"} in entry["properties"]["skipped"][
        "anyOf"
    ]
    # the api always writes every field, so none is optional in the types
    assert schema["required"] == ["entries", "skipped"]
    assert entry["required"] == ["issues", "skipped"]


def test_the_report_schema_has_no_validation() -> None:
    """The report is answered without its validation."""
    schema = json.loads(schema_json())
    assert "validation" not in schema["$defs"]["Report"]["properties"]


def test_main_writes_every_schema_into_the_directory(tmp_path: Path) -> None:
    """`main` writes the report, annotation and validation schema into a directory."""
    from sbml4humans.schema import annotation_schema_json, main, validation_schema_json

    main(["schema", str(tmp_path / "out")])
    out = tmp_path / "out"
    assert (out / "report.schema.json").read_text(encoding="utf-8") == schema_json()
    assert (out / "annotation.schema.json").read_text(
        encoding="utf-8"
    ) == annotation_schema_json()
    assert (out / "validation.schema.json").read_text(
        encoding="utf-8"
    ) == validation_schema_json()
