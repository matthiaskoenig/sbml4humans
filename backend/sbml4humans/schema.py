"""The JSON schemas of the api: the report, the annotation resource, the validation.

The frontend generates its TypeScript types from the schema, which mirrors the
pydantic model by construction. Run `python -m sbml4humans.schema` after a
change of a model and commit the schemas.
"""

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema

from sbml4humans.annotations import AnnotationResource
from sbml4humans.model import ReportResponse, ValidationResponse


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "schema"
SCHEMA_PATH = SCHEMA_DIR / "report.schema.json"
ANNOTATION_SCHEMA_PATH = SCHEMA_DIR / "annotation.schema.json"
VALIDATION_SCHEMA_PATH = SCHEMA_DIR / "validation.schema.json"


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


def _schema_json(model: type[BaseModel]) -> str:
    """The JSON schema of a model with camelCase properties."""
    schema = model.model_json_schema(
        by_alias=True, schema_generator=_GenerateJsonSchemaWithoutPropertyTitles
    )
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def schema_json() -> str:
    """The JSON schema of `ReportResponse` with camelCase properties."""
    return _schema_json(ReportResponse)


def annotation_schema_json() -> str:
    """The JSON schema of `AnnotationResource` with camelCase properties."""
    return _schema_json(AnnotationResource)


def validation_schema_json() -> str:
    """The JSON schema of `ValidationResponse` with camelCase properties."""
    return _schema_json(ValidationResponse)


def main(argv: list[str]) -> None:
    """Write every schema into the given directory or into `SCHEMA_DIR`."""
    directory = Path(argv[1]) if len(argv) > 1 else SCHEMA_DIR
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in (
        (SCHEMA_PATH.name, schema_json()),
        (ANNOTATION_SCHEMA_PATH.name, annotation_schema_json()),
        (VALIDATION_SCHEMA_PATH.name, validation_schema_json()),
    ):
        (directory / name).write_text(text, encoding="utf-8")
        print(f"schema written to {directory / name}")


if __name__ == "__main__":
    main(sys.argv)
