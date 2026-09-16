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


def test_committed_schema_is_current() -> None:
    """The schema of the frontend equals the schema of the current model."""
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_json(), (
        "run `uv run python -m sbml4humans.schema` and commit the schema"
    )
