"""The JSON schema of the api response.

The frontend generates its TypeScript types from the schema, which mirrors the
pydantic model by construction. Run `python -m sbml4humans.schema` after a
change of the model and commit the schema.
"""

import json
import sys
from pathlib import Path
from typing import Any

from pydantic.json_schema import GenerateJsonSchema

from sbml4humans.model import ReportResponse


SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "src"
    / "schema"
    / "report.schema.json"
)


class _GenerateJsonSchemaWithoutPropertyTitles(GenerateJsonSchema):
    """A schema generator that titles `$defs` entries but not their properties.

    Pydantic titles every property by default (`"title": "Sbmltype"`), which
    makes json-schema-to-typescript hoist every titled property into its own
    named alias (`Sbmltype6`, `Value3`, ...) instead of reusing the type of
    the `$defs` entry.
    """

    def field_title_should_be_set(self, schema: Any) -> bool:
        """Never title a property, `$defs` entries keep their class name."""
        return False


def schema_json() -> str:
    """The JSON schema of `ReportResponse` with camelCase properties."""
    schema = ReportResponse.model_json_schema(
        by_alias=True, schema_generator=_GenerateJsonSchemaWithoutPropertyTitles
    )
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> None:
    """Write the schema to the given path or to `SCHEMA_PATH`."""
    path = Path(argv[1]) if len(argv) > 1 else SCHEMA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(schema_json(), encoding="utf-8")
    print(f"schema written to {path}")


if __name__ == "__main__":
    main(sys.argv)
