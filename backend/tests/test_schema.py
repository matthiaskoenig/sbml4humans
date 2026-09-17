"""Tests of the JSON schema export."""

import json

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


def test_committed_schema_is_current() -> None:
    """The schema of the frontend equals the schema of the current model."""
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_json(), (
        "run `uv run python -m sbml4humans.schema` and commit the schema"
    )
