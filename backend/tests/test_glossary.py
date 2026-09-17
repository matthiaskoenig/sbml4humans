"""Tests of the glossary generator."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from sbml4humans import glossary as glossary_module
from sbml4humans.glossary import (
    Glossary,
    GlossaryError,
    check,
    main,
    render_json,
    render_type_page,
    write,
)


FIXTURE = Path(__file__).parent / "data" / "glossary"

# the properties every element of the report model carries, as the schema of a
# report writes them
SBASE_FIELDS: dict[str, Any] = {
    "pk": {"type": "string"},
    "sbmlType": {"type": "string"},
    "id": {"type": "string"},
    "metaId": {"type": "string"},
    "name": {"type": "string"},
    "sbo": {"type": "string"},
    "notes": {"type": "string"},
    "cvterms": {"items": {"$ref": "#/$defs/CVTerm"}, "type": "array"},
    "history": {"anyOf": [{"$ref": "#/$defs/ModelHistory"}, {"type": "null"}]},
    "xml": {"type": "string"},
    "comp": {"anyOf": [{"$ref": "#/$defs/CompSBase"}, {"type": "null"}]},
}


def _report_schema(species: dict[str, Any] | None = None) -> dict[str, Any]:
    """A report schema with the two types of the fixture glossary."""
    return {
        "$defs": {
            "CVTerm": {"properties": {"qualifier": {"type": "string"}}},
            "CompSBase": {
                "properties": {
                    "replacedBy": {"type": "string"},
                    "replacedElements": {"type": "array"},
                }
            },
            "ModelHistory": {"properties": {"creators": {"type": "array"}}},
            "Compartment": {"properties": dict(SBASE_FIELDS)},
            "Species": {
                "properties": {
                    **SBASE_FIELDS,
                    "initialAmount": {"type": "number"},
                    "derivedUnits": {"type": "string"},
                    **(species or {}),
                }
            },
        }
    }


def _repository(
    tmp_path: Path,
    *,
    schema: dict[str, Any] | None = None,
    kinds: tuple[str, ...] = ("compartment",),
    extra_glossary: str = "",
) -> Path:
    """A repository with the fixture glossary, a report schema and the edge kinds."""
    shutil.copytree(FIXTURE, tmp_path / "glossary")
    if extra_glossary:
        (tmp_path / "glossary" / "extra.toml").write_text(
            extra_glossary, encoding="utf-8"
        )
    schema_path = tmp_path / "frontend" / "src" / "schema" / "report.schema.json"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(
        json.dumps(schema if schema is not None else _report_schema()), encoding="utf-8"
    )
    kinds_path = tmp_path / "frontend" / "src" / "data" / "edgeKinds.ts"
    kinds_path.parent.mkdir(parents=True, exist_ok=True)
    listed = ",\n  ".join(f'"{kind}"' for kind in kinds)
    kinds_path.write_text(
        f"export const EDGE_KINDS: readonly EdgeKind[] = [\n  {listed},\n];\n",
        encoding="utf-8",
    )
    return tmp_path


def test_reads_the_entries() -> None:
    """Every section of a glossary file becomes an entry."""
    glossary = Glossary.from_directory(FIXTURE)
    assert glossary.types["Species"].label == "Species"
    assert glossary.types["Species"].attributes["initialAmount"].summary
    assert glossary.links["compartment"].label == "compartment"
    assert glossary.concepts["derivedUnits"].label == "derived units"


def test_renders_the_page_of_a_type() -> None:
    """The page of a type has its attributes, its related types and its source."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    assert page.startswith("# Species\n")
    assert "| [initial amount](#initial-amount) |" in page
    assert "[Compartment](compartment.md)" in page
    assert "SBML Level 3 Version 2 Core" in page


def test_renders_the_description_of_every_attribute() -> None:
    """The prose of an attribute is rendered below the table, with its anchor."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    initial_amount = glossary.types["Species"].attributes["initialAmount"]
    assert f'<span id="initial-amount"></span>**{initial_amount.label}**' in page
    assert initial_amount.description in page
    # the anchor of the row is the description block, not the cell of the table
    assert '| <span id="initial-amount"></span>' not in page
    # a field of the report is rendered the same way, below its own table
    assert '<span id="derived-units"></span>**derived units**' in page


def test_every_type_page_points_at_the_shared_attributes() -> None:
    """A type without an attribute table still points at `SBase`."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Compartment"])
    assert "## Attributes" not in page
    assert "[common attributes](sbase.md)" in page


def test_the_specification_column_names_the_document() -> None:
    """A section of a table says which specification it belongs to."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    assert "[core 4.6.4](" in page


def test_renders_the_json_without_the_descriptions() -> None:
    """The application reads the labels and the summaries, not the prose."""
    glossary = Glossary.from_directory(FIXTURE)
    data = render_json(glossary)
    assert data["types"]["Species"]["summary"]
    assert "description" not in data["types"]["Species"]
    assert (
        data["types"]["Species"]["attributes"]["initialAmount"]["label"]
        == "initial amount"
    )
    assert data["links"]["compartment"]["summary"]
    assert data["concepts"]["derivedUnits"]["summary"]


def test_a_missing_summary_is_an_error(tmp_path: Path) -> None:
    """An entry without a summary has no tooltip, which is an error."""
    (tmp_path / "core.toml").write_text('[types.Species]\nlabel = "Species"\n')
    with pytest.raises(GlossaryError, match="summary"):
        Glossary.from_directory(tmp_path)


def test_a_broken_page_link_is_an_error(tmp_path: Path) -> None:
    """A description which links a page that is not generated is an error."""
    (tmp_path / "core.toml").write_text(
        '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
        'description = "see [Nothing](nothing.md)"\n'
    )
    glossary = Glossary.from_directory(tmp_path)
    with pytest.raises(GlossaryError, match=r"nothing\.md"):
        glossary.validate_links()


def test_a_link_to_a_page_of_the_site_resolves(tmp_path: Path) -> None:
    """A description may link a page outside the reference with `../`."""
    (tmp_path / "core.toml").write_text(
        '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
        'description = "see [SBML](../sbml.md)"\n'
    )
    glossary = Glossary.from_directory(tmp_path)
    glossary.validate_links()


def test_check_reports_a_stale_page(tmp_path: Path) -> None:
    """A committed page which the glossary does not generate is stale."""
    root = _repository(tmp_path)
    glossary = Glossary.from_directory(root / "glossary")
    write(glossary, root)
    check(root, glossary)
    page = root / "docs" / "reference" / "species.md"
    page.write_text(page.read_text(encoding="utf-8") + "by hand\n", encoding="utf-8")
    with pytest.raises(GlossaryError, match=r"docs/reference/species\.md"):
        check(root, glossary)


def test_check_reports_a_stale_json(tmp_path: Path) -> None:
    """The json of the application is stale when the glossary changed."""
    root = _repository(tmp_path)
    glossary = Glossary.from_directory(root / "glossary")
    write(glossary, root)
    data = root / "frontend" / "src" / "data" / "glossary.json"
    data.write_text(data.read_text(encoding="utf-8").replace("Species", "Spezies"))
    with pytest.raises(GlossaryError, match=r"frontend/src/data/glossary\.json"):
        check(root, glossary)


def test_check_reports_a_page_of_a_removed_type(tmp_path: Path) -> None:
    """A page which no entry generates any more is reported."""
    root = _repository(tmp_path)
    glossary = Glossary.from_directory(root / "glossary")
    write(glossary, root)
    (root / "docs" / "reference" / "orphan.md").write_text("# Orphan\n")
    with pytest.raises(GlossaryError, match=r"orphan\.md"):
        check(root, glossary)


def test_coverage_requires_an_entry_for_every_field(tmp_path: Path) -> None:
    """A field of the report model without an entry fails the check."""
    root = _repository(
        tmp_path, schema=_report_schema({"initialConcentration": {"type": "number"}})
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match=r"Species\.initialConcentration"):
        glossary.validate_coverage(root)


def test_coverage_requires_an_entry_for_a_nested_field(tmp_path: Path) -> None:
    """A field of an object an element carries inline needs its own entry."""
    root = _repository(tmp_path)
    text = (root / "glossary" / "core.toml").read_text(encoding="utf-8")
    start = text.index('[types.SBase.attributes."comp.replacedBy"]')
    end = text.index('[types.SBase.attributes."comp.replacedElements"]')
    (root / "glossary" / "core.toml").write_text(
        text[:start] + text[end:], encoding="utf-8"
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match=r"comp\.replacedBy has no entry"):
        glossary.validate_coverage(root)


def test_coverage_requires_an_entry_for_every_link_kind(tmp_path: Path) -> None:
    """A kind of `edgeKinds.ts` without an entry fails the check."""
    root = _repository(tmp_path, kinds=("compartment", "units"))
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match="the link kind units has no entry"):
        glossary.validate_coverage(root)


def test_coverage_rejects_a_type_which_the_report_does_not_have(tmp_path: Path) -> None:
    """A mistyped type key generates a page nobody reaches, so it is an error."""
    root = _repository(
        tmp_path,
        extra_glossary=(
            '[types.Speceis]\nlabel = "Speceis"\nsummary = "a typo"\n'
            'description = "A type which the report does not have."\n'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match="Speceis"):
        glossary.validate_coverage(root)


def test_coverage_reports_a_missing_report_model(tmp_path: Path) -> None:
    """The check says which file is missing instead of raising an OSError."""
    root = _repository(tmp_path)
    (root / "frontend" / "src" / "schema" / "report.schema.json").unlink()
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match=r"report\.schema\.json"):
        glossary.validate_coverage(root)


def test_main_writes_the_files_and_checks_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--check` fails on a repository which was not regenerated and passes after."""
    root = _repository(tmp_path)
    monkeypatch.setattr(glossary_module, "REPO_ROOT", root)
    assert main(["glossary", "--check"]) == 1
    assert main(["glossary"]) == 0
    assert main(["glossary", "--check"]) == 0
