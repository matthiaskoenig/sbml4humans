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
    pages = Glossary.from_directory(tmp_path / "glossary").pages()
    _write_navigation(tmp_path, [f"reference/{name}" for name in sorted(pages)])
    return tmp_path


def _write_navigation(root: Path, pages: list[str]) -> None:
    """The configuration of the site, with the pages its navigation lists."""
    entries = ",\n    ".join(f'{{ "page" = "{page}" }}' for page in pages)
    (root / "zensical.toml").write_text(
        f'[project]\nnav = [\n  {{ "Reference" = [\n    {entries},\n  ] }},\n]\n',
        encoding="utf-8",
    )


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


def _glossary_file(tmp_path: Path, content: str) -> Glossary:
    """A glossary of one file, for the tests of a single rule."""
    (tmp_path / "core.toml").write_text(content, encoding="utf-8")
    return Glossary.from_directory(tmp_path)


def _species_with(tmp_path: Path, description: str) -> Glossary:
    """A glossary of one type with one attribute, and the description to check."""
    return _glossary_file(
        tmp_path,
        '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
        f"description = '''{description}'''\n"
        "[types.Species.attributes.initialAmount]\n"
        'label = "initial amount"\nsummary = "the amount at the start"\n'
        'description = "The amount of the species when the simulation starts."\n',
    )


def test_two_attributes_with_the_same_label_get_their_own_anchor(
    tmp_path: Path,
) -> None:
    """Two attributes of one page which share a label do not share an anchor."""
    glossary = _glossary_file(
        tmp_path,
        '[types.Reaction]\nlabel = "Reaction"\nsummary = "a conversion of species"\n'
        'description = "A reaction converts species into other species."\n'
        "[types.Reaction.attributes.kineticLaw]\n"
        'label = "kinetic law"\nsummary = "the law which gives the speed"\n'
        'description = "The kinetic law of the reaction."\n'
        '[types.Reaction.attributes."kineticLaw.math"]\n'
        'label = "kinetic law"\npackage = "report"\n'
        'summary = "the formula the report renders"\n'
        'description = "The formula of the kinetic law as the report shows it."\n',
    )
    page = render_type_page(glossary, glossary.types["Reaction"])
    assert '<span id="kinetic-law"></span>' in page
    assert '<span id="kinetic-law-2"></span>' in page
    # the row of the attribute links its own block, not the block of the other
    assert "| [kinetic law](#kinetic-law) | - | the law which gives the speed |" in page
    assert (
        "| [kinetic law](#kinetic-law-2) | - | the formula the report renders |" in page
    )
    anchors = glossary_module._anchors_of(page)
    assert sorted(anchors) == sorted(set(anchors))


def test_every_generated_page_has_unique_anchors() -> None:
    """No page of the generated reference carries the same id twice."""
    root = glossary_module.REPO_ROOT
    glossary = Glossary.from_directory(root / glossary_module.GLOSSARY_DIR)
    for name, page in glossary_module._reference_pages(glossary).items():
        anchors = glossary_module._anchors_of(page)
        duplicates = sorted({a for a in anchors if anchors.count(a) > 1})
        assert not duplicates, f"{name}: {', '.join(duplicates)}"


def test_a_fragment_link_resolves_to_an_anchor_of_the_page(tmp_path: Path) -> None:
    """A description may link an anchor of its own page and of another page."""
    glossary = _species_with(
        tmp_path,
        "see [the amount](#initial-amount) and [it again](species.md#initial-amount)",
    )
    glossary.validate_links()


def test_a_broken_fragment_link_is_an_error(tmp_path: Path) -> None:
    """A link to an anchor which no page carries is an error."""
    glossary = _species_with(tmp_path, "see [the amount](species.md#no-such-anchor)")
    with pytest.raises(GlossaryError, match="no-such-anchor"):
        glossary.validate_links()
    glossary = _species_with(tmp_path, "see [the amount](#no-such-anchor)")
    with pytest.raises(GlossaryError, match="no-such-anchor"):
        glossary.validate_links()


def test_coverage_reports_a_report_model_without_an_sbase(tmp_path: Path) -> None:
    """A renamed field of `SBase` is an error, not a `TypeError`."""
    root = _repository(
        tmp_path, schema={"$defs": {"Species": {"properties": {"sid": {}}}}}
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match="SBase"):
        glossary.validate_coverage(root)


def test_coverage_rejects_an_attribute_which_the_report_does_not_have(
    tmp_path: Path,
) -> None:
    """A mistyped attribute key describes a field which no element has."""
    root = _repository(
        tmp_path,
        extra_glossary=(
            "[types.Species.attributes.initialAmountt]\n"
            'label = "initial amountt"\nsummary = "a typo"\n'
            'description = "A field which the report does not have."\n'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(
        GlossaryError, match=r"types\.Species\.attributes\.initialAmountt"
    ):
        glossary.validate_coverage(root)


def test_coverage_accepts_the_glossary_of_the_repository() -> None:
    """The glossary of the repository covers the report in both directions."""
    root = glossary_module.REPO_ROOT
    Glossary.from_directory(root / glossary_module.GLOSSARY_DIR).validate_coverage(root)


def test_a_missing_image_is_an_error(tmp_path: Path) -> None:
    """A page which shows an image that does not exist is an error."""
    root = _repository(tmp_path)
    page = root / "docs" / "index.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("# Home\n\n![the report](images/report.png)\n", encoding="utf-8")
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match=r"images/report\.png"):
        glossary.validate_links(root)
    (root / "docs" / "images").mkdir(parents=True)
    (root / "docs" / "images" / "report.png").write_bytes(b"")
    glossary.validate_links(root)


def test_a_link_to_a_page_of_the_site_is_checked_against_the_documentation(
    tmp_path: Path,
) -> None:
    """With a root, a `../` link has to name a page of `docs/`."""
    root = _repository(tmp_path)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "sbml.md").write_text("# SBML\n\n## The model\n", encoding="utf-8")
    text = (root / "glossary" / "core.toml").read_text(encoding="utf-8")
    (root / "glossary" / "core.toml").write_text(
        text.replace(
            "A compartment is the space a species lives in",
            "See [SBML](../sbml.md#the-model). A compartment is the space a species "
            "lives in",
        ),
        encoding="utf-8",
    )
    glossary = Glossary.from_directory(root / "glossary")
    glossary.validate_links(root)
    (root / "docs" / "sbml.md").unlink()
    with pytest.raises(GlossaryError, match=r"\.\./sbml\.md"):
        glossary.validate_links(root)


def test_a_summary_which_ends_with_a_period_is_an_error(tmp_path: Path) -> None:
    """The summary is one sentence shown as a tooltip, without a period."""
    with pytest.raises(GlossaryError, match="period"):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species."\n'
            'description = "A pool of a chemical entity."\n',
        )


def test_an_unknown_key_of_an_entry_is_an_error(tmp_path: Path) -> None:
    """A key the format does not define is most likely a typo."""
    with pytest.raises(GlossaryError, match="summry"):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\nsummry = "a typo"\n',
        )


def test_an_unknown_spec_document_is_an_error(tmp_path: Path) -> None:
    """An entry may only cite a document the glossary defines."""
    with pytest.raises(GlossaryError, match="l3v1"):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\n'
            'spec = { doc = "l3v1", section = "4.6" }\n',
        )


def test_an_unknown_related_type_is_an_error(tmp_path: Path) -> None:
    """A related type which has no entry would render a link to nothing."""
    with pytest.raises(GlossaryError, match="Compartment"):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\n'
            'related = ["Compartment"]\n',
        )


def test_a_key_defined_in_two_files_is_an_error(tmp_path: Path) -> None:
    """Two files may not explain the same thing twice."""
    entry = (
        '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
        'description = "A pool of a chemical entity."\n'
    )
    (tmp_path / "core.toml").write_text(entry, encoding="utf-8")
    (tmp_path / "packages.toml").write_text(entry, encoding="utf-8")
    with pytest.raises(GlossaryError, match=r"core\.toml"):
        Glossary.from_directory(tmp_path)


def test_an_unknown_section_of_a_file_is_an_error(tmp_path: Path) -> None:
    """A misspelled table name would silently drop every entry below it."""
    with pytest.raises(GlossaryError, match="typess"):
        _glossary_file(
            tmp_path,
            '[typess.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\n',
        )


def test_a_type_which_is_not_a_string_is_an_error(tmp_path: Path) -> None:
    """The `type` of an entry is rendered into the table, so it is a string."""
    with pytest.raises(GlossaryError, match="type"):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\ntype = 12\n',
        )


def test_check_reports_a_generated_page_the_navigation_does_not_list(
    tmp_path: Path,
) -> None:
    """A new type generates a page, which the navigation of the site has to list."""
    root = _repository(tmp_path)
    glossary = Glossary.from_directory(root / "glossary")
    glossary.validate_navigation(root)
    _write_navigation(
        root,
        [
            f"reference/{name}"
            for name in sorted(glossary.pages())
            if name != "species.md"
        ],
    )
    with pytest.raises(GlossaryError, match=r"reference/species\.md"):
        glossary.validate_navigation(root)
