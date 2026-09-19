"""Tests of the glossary generator."""

import json
import re
import shutil
import tomllib
from pathlib import Path
from types import UnionType
from typing import Annotated, Any, Union, get_args, get_origin

import pytest

from sbml4humans import glossary as glossary_module
from sbml4humans.glossary import (
    DOCS_URL,
    Glossary,
    GlossaryError,
    check,
    main,
    render_datatypes_page,
    render_details,
    render_json,
    render_type_page,
    write,
)
from sbml4humans.glossaryrules import resolve_rule
from sbml4humans.model import Model


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
    assert "| [initialAmount](#initialamount) |" in page
    assert "[Compartment](compartment.md)" in page
    assert "SBML Level 3 Version 2 Core" in page


def test_renders_the_description_of_every_attribute() -> None:
    """The prose of an attribute is rendered below the table, with its anchor."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    initial_amount = glossary.types["Species"].attributes["initialAmount"]
    assert f'<span id="initialamount"></span>**{initial_amount.label}**' in page
    assert initial_amount.description in page
    # the anchor of the row is the description block, not the cell of the table
    assert '| <span id="initialamount"></span>' not in page
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
        == "initialAmount"
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


def _attribute(type_name: str, name: str, body: str) -> str:
    """A complete attribute table added to an existing type, plus the body under test.

    Used by the tests of the technical checks, which only care about the keys
    `body` adds: `rules`, `required` or `package`. `label`, `type`, `spec`,
    `summary` and `description` are filled in so the attribute is otherwise a
    valid one.
    """
    return (
        f"[types.{type_name}.attributes.{name}]\n"
        f'label = "{name}"\n'
        'type = "string"\n'
        'spec = { doc = "l3v2", section = "4.6" }\n'
        'summary = "a technical detail for the tests"\n'
        'description = "An attribute added only to exercise the technical checks."\n'
        f"{body}\n"
    )


def _species_with(tmp_path: Path, description: str) -> Glossary:
    """A glossary of one type with one attribute, and the description to check."""
    return _glossary_file(
        tmp_path,
        '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
        f"description = '''{description}'''\n"
        "[types.Species.attributes.initialAmount]\n"
        'label = "initialAmount"\nsummary = "the amount at the start"\n'
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
    assert (
        "| [kinetic law](#kinetic-law) | - | - | the law which gives the speed |"
        in page
    )
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


def test_the_docs_anchor_of_a_data_type_is_an_anchor_of_its_page() -> None:
    """The `docs` url of a data type points at an anchor `datatypes.md` really has.

    The details and `render_datatypes_page` compute the anchor of a data type
    through the same helper, so a `docs` url can never point at an anchor the
    rendered page does not offer.
    """
    glossary = Glossary.from_directory(FIXTURE)
    page = render_datatypes_page(glossary)
    anchors = set(glossary_module._anchors_of(page))
    entries = render_details(glossary)["entries"]
    for key in glossary.datatypes:
        docs = entries[f"datatypes/{key}"]["docs"]
        _, _, fragment = docs.partition("#")
        assert fragment in anchors, f"{key}: '{fragment}' is not an anchor of the page"


def test_a_fragment_link_resolves_to_an_anchor_of_the_page(tmp_path: Path) -> None:
    """A description may link an anchor of its own page and of another page."""
    glossary = _species_with(
        tmp_path,
        "see [the amount](#initialamount) and [it again](species.md#initialamount)",
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
            'label = "initialAmountt"\nsummary = "a typo"\n'
            'description = "A field which the report does not have."\n'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(
        GlossaryError, match=r"types\.Species\.attributes\.initialAmountt"
    ):
        glossary.validate_coverage(root)


def test_an_attribute_of_a_specification_is_labelled_by_its_name(
    tmp_path: Path,
) -> None:
    """A label in plain words is for what the report adds, not for the specification."""
    root = _repository(
        tmp_path,
        extra_glossary=(
            "[types.Species.attributes.boundaryCondition]\n"
            'label = "boundary condition"\nsummary = "a flag"\n'
            'spec = { doc = "l3v2", section = "4.6.6" }\n'
            'description = "Whether the reactions leave the species unchanged."\n'
            '[types.Species.attributes."fbc.charge"]\n'
            'label = "fbc:charge"\nsummary = "the charge"\n'
            'spec = { doc = "l3v2" }\n'
            'description = "An attribute a package adds carries its prefix."\n'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError) as error:
        glossary.validate_labels()
    message = str(error.value)
    assert "types.Species.attributes.boundaryCondition" in message
    assert "'boundary condition'" in message
    # the name with the prefix of its package is a name, and so are the words of an
    # attribute which cites no specification, the derived units of the fixture
    assert "fbc.charge" not in message
    assert "derivedUnits" not in message


def test_a_type_is_labelled_by_its_name(tmp_path: Path) -> None:
    """The label of a type is the name of its class."""
    (tmp_path / "core.toml").write_text(
        '[types.FunctionDefinition]\nlabel = "Function definition"\n'
        'summary = "a function"\ndescription = "A named formula."\n',
        encoding="utf-8",
    )
    with pytest.raises(GlossaryError, match="not by its name 'FunctionDefinition'"):
        Glossary.from_directory(tmp_path).validate_labels()


def test_a_link_kind_is_labelled_by_its_key(tmp_path: Path) -> None:
    """The group of links is named as the attribute which makes the reference."""
    (tmp_path / "report.toml").write_text(
        '[links.kineticLaw]\nlabel = "kinetic law"\n'
        'summary = "the law of a reaction"\ndescription = "A reaction names its law."\n',
        encoding="utf-8",
    )
    with pytest.raises(GlossaryError, match="not by its name 'kineticLaw'"):
        Glossary.from_directory(tmp_path).validate_labels()


def test_the_labels_of_the_repository_are_names() -> None:
    """The glossary of the repository names what the specification names."""
    root = glossary_module.REPO_ROOT
    Glossary.from_directory(root / glossary_module.GLOSSARY_DIR).validate_labels()


def test_coverage_accepts_the_glossary_of_the_repository() -> None:
    """The glossary of the repository covers the report in both directions."""
    root = glossary_module.REPO_ROOT
    Glossary.from_directory(root / glossary_module.GLOSSARY_DIR).validate_coverage(root)


def _classes(annotation: Any) -> list[Any]:
    """The classes an annotation names, through a list, a union and a metadata."""
    origin = get_origin(annotation)
    if origin is Annotated:
        return _classes(get_args(annotation)[0])
    if origin in (list, Union, UnionType):
        return [cls for arg in get_args(annotation) for cls in _classes(arg)]
    return [annotation]


def test_a_package_page_names_every_section_the_package_adds() -> None:
    """The page of a package links every type it gives a section of a model.

    Every list of a model is a section of the report, so the page which says
    what the report shows of a package names each of them.
    """
    root = glossary_module.REPO_ROOT
    glossary = Glossary.from_directory(root / glossary_module.GLOSSARY_DIR)
    missing: list[str] = []
    for name, field in Model.model_fields.items():
        if not name.startswith("list_of_"):
            continue
        for cls in _classes(field.annotation):
            entry = glossary.types[cls.__name__]
            if entry.package == "core":
                continue
            if f"({entry.slug}.md)" not in glossary.types[entry.package].description:
                missing.append(f"{entry.package} names no {cls.__name__}")
    assert missing == []


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
    _write_navigation(
        root,
        [
            f"reference/{name}"
            for name in sorted(glossary.pages())
            if name != "datatypes.md"
        ],
    )
    with pytest.raises(GlossaryError, match=r"reference/datatypes\.md"):
        glossary.validate_navigation(root)


def test_reads_the_technical_details() -> None:
    """`required`, `default`, `rules` and the `datatypes` section are read."""
    glossary = Glossary.from_directory(FIXTURE)
    initial_amount = glossary.types["Species"].attributes["initialAmount"]
    assert initial_amount.required is False
    assert initial_amount.default == "set by an initial assignment or a rule"
    assert initial_amount.rules == (20609,)
    assert glossary.types["Species"].rules == (20601,)
    assert glossary.datatypes["double"].label == "double"
    assert glossary.datatypes["SBOTerm"].values == (
        "entity",
        "participant role",
        "modeling framework",
    )
    assert glossary.type_key("double") == "datatypes/double"
    assert glossary.type_key("Species") == "types/Species"
    assert glossary.type_key("nothing") is None
    assert [rule.id for rule in glossary.resolved_rules(initial_amount)] == [20609]
    # the fixture states nothing which validate_technical rejects
    glossary.validate_technical()


def test_the_attribute_table_states_required() -> None:
    """The table of the attributes states whether each one is required."""
    glossary = Glossary.from_directory(FIXTURE)
    species_page = render_type_page(glossary, glossary.types["Species"])
    assert "| attribute | type | required | meaning | specification |" in species_page
    assert (
        "| [initialAmount](#initialamount) | [`double`](datatypes.md#double) | "
        "optional | the amount of the species when the simulation starts |"
    ) in species_page
    # an attribute which states nothing shows a dash, not an empty cell
    sbase_page = render_type_page(glossary, glossary.types["SBase"])
    assert (
        "| [id](#id) | [`SId`](datatypes.md#sid) | - | the identifier of the element |"
        in sbase_page
    )


def test_an_attribute_states_its_default_and_its_rules() -> None:
    """The block of an attribute states its default and lists the rules it cites."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    assert "Default: set by an initial assignment or a rule." in page
    rule = resolve_rule(20609)
    assert f"- `{rule.id}` ({rule.severity}): " in page
    # the angle brackets of the message show up literally, not as an html tag
    assert "&lt;species&gt;" in page
    assert "<species>" not in page


def test_a_type_page_lists_its_rules() -> None:
    """A type which cites a validation rule lists it under its own heading."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    rule = resolve_rule(20601)
    assert "## Validation rules" in page
    assert f"- `{rule.id}` ({rule.severity}): " in page
    assert "&lt;compartment&gt;" in page
    # the section comes before "Related elements", which the fixture also has
    assert page.index("## Validation rules") < page.index("## Related elements")


def test_the_type_of_an_attribute_links_its_data_type(tmp_path: Path) -> None:
    """The `type` column links its data type, or the page of a type it names."""
    root = _repository(
        tmp_path,
        extra_glossary=(
            '[types.Species.attributes.extra]\nlabel = "extra"\n'
            'type = "Compartment"\nsummary = "for the test only"\n'
            'description = "An attribute added only to exercise the type link."\n'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    page = render_type_page(glossary, glossary.types["Species"])
    # the data type of another attribute links datatypes.md
    assert "[`double`](datatypes.md#double)" in page
    # a `type` which names a type of the glossary links its own page
    assert "[`Compartment`](compartment.md)" in page


def test_renders_the_page_of_the_data_types() -> None:
    """`datatypes.md` has one section per data type, with its values and its source."""
    glossary = Glossary.from_directory(FIXTURE)
    page = render_datatypes_page(glossary)
    assert page.startswith("# Data types\n")
    assert "## `double`" in page
    assert "A double is a number written in decimal notation" in page
    assert "- `entity`" in page
    assert "- `participant role`" in page
    assert "- `modeling framework`" in page


def test_the_data_types_page_renders_without_a_data_type(tmp_path: Path) -> None:
    """The page is rendered even when the glossary has no data type yet."""
    glossary = _glossary_file(tmp_path, "")
    page = render_datatypes_page(glossary)
    assert page.startswith("# Data types\n")
    assert "##" not in page


def test_required_is_a_boolean(tmp_path: Path) -> None:
    """`required` is read as a boolean, not as a string a reader might write."""
    with pytest.raises(GlossaryError, match="'required' is not a boolean"):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\n'
            "[types.Species.attributes.initialAmount]\n"
            'label = "initialAmount"\nsummary = "the amount at the start"\n'
            'description = "The amount of the species when the simulation starts."\n'
            'required = "yes"\n',
        )


def test_a_default_of_a_required_attribute_is_an_error(tmp_path: Path) -> None:
    """A required attribute is always present, so a default makes no sense."""
    with pytest.raises(
        GlossaryError, match="'default' is given for a required attribute"
    ):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\n'
            "[types.Species.attributes.initialAmount]\n"
            'label = "initialAmount"\nsummary = "the amount at the start"\n'
            'description = "The amount of the species when the simulation starts."\n'
            'required = true\ndefault = "0"\n',
        )


def test_a_rule_listed_twice_is_an_error(tmp_path: Path) -> None:
    """A rule cited twice in the same list is most likely a copy-paste mistake."""
    with pytest.raises(GlossaryError, match="the rule 20609 is listed twice"):
        _glossary_file(
            tmp_path,
            '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
            'description = "A pool of a chemical entity."\n'
            "[types.Species.attributes.initialAmount]\n"
            'label = "initialAmount"\nsummary = "the amount at the start"\n'
            'description = "The amount of the species when the simulation starts."\n'
            "rules = [20609, 20609]\n",
        )


def test_an_unknown_rule_is_an_error(tmp_path: Path) -> None:
    """A rule number has to resolve against the validation rules of libsbml."""
    root = _repository(
        tmp_path,
        extra_glossary=_attribute(
            "Species", "extra", "required = false\nrules = [99999]"
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(
        GlossaryError, match=r"extra\.toml: types\.Species\.attributes\.extra.*99999"
    ):
        glossary.validate_technical()


def test_a_rule_of_a_foreign_package_is_an_error(tmp_path: Path) -> None:
    """A rule cited by an entry belongs to core or to the package of the entry."""
    root = _repository(
        tmp_path,
        extra_glossary=_attribute(
            "Species", "extra", 'package = "fbc"\nrules = [1020101]'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(
        GlossaryError,
        match=r"the rule 1020101 is a rule of comp, the entry belongs to fbc",
    ):
        glossary.validate_technical()


def test_an_attribute_of_the_report_cannot_be_required(tmp_path: Path) -> None:
    """An attribute the report adds cites no specification, so it is never required."""
    root = _repository(
        tmp_path,
        extra_glossary=(
            '[types.Species.attributes.extra]\nlabel = "extra"\n'
            'package = "report"\ntype = "string"\n'
            'summary = "a field the report adds"\n'
            'description = "A field which cites no specification."\n'
            "required = false\n"
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(
        GlossaryError,
        match=r"extra\.toml: types\.Species\.attributes\.extra.*cannot be required",
    ):
        glossary.validate_technical()


def test_a_type_which_names_nothing_is_an_error(tmp_path: Path) -> None:
    """The `type` of an entry has to be a data type or a type of the glossary."""
    root = _repository(
        tmp_path,
        extra_glossary=(
            '[types.Species.attributes.extra]\nlabel = "extra"\n'
            'type = "Foo"\nsummary = "a technical detail for the tests"\n'
            'description = "An attribute added only to exercise the technical checks."\n'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(
        GlossaryError,
        match=r"the type 'Foo' is neither a data type nor a type of the glossary",
    ):
        glossary.validate_types()


def test_an_unused_data_type_is_an_error(tmp_path: Path) -> None:
    """A data type no attribute names and no data type relates to is unused."""
    root = _repository(tmp_path)
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(
        GlossaryError, match=r"datatypes\.SIdRef: the data type is not used"
    ):
        glossary.validate_types()


def test_required_is_demanded_for_an_attribute_of_a_specification(
    tmp_path: Path,
) -> None:
    """Every attribute which cites a specification has to state `required`."""
    root = _repository(
        tmp_path,
        extra_glossary=(
            '[types.Species.attributes.extra]\nlabel = "extra"\n'
            'spec = { doc = "l3v2", section = "4.6" }\n'
            'summary = "a technical detail for the tests"\n'
            'description = "An attribute added only to exercise the technical checks."\n'
        ),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match=r"does not state whether it is required"):
        glossary.validate_required()


def test_an_unknown_key_of_a_data_type_is_an_error(tmp_path: Path) -> None:
    """A key the format of a data type does not define is most likely a typo."""
    with pytest.raises(GlossaryError, match="summry"):
        _glossary_file(
            tmp_path,
            '[datatypes.double]\nlabel = "double"\nsummary = "a number"\n'
            'description = "A floating point number."\nsummry = "a typo"\n',
        )


def test_the_details_carry_the_technical_details() -> None:
    """An attribute with every technical field renders each of them."""
    glossary = Glossary.from_directory(FIXTURE)
    initial_amount = glossary.types["Species"].attributes["initialAmount"]
    rule = resolve_rule(20609)
    entry = render_details(glossary)["entries"]["types/Species/initialAmount"]
    assert entry["kind"] == "attribute"
    assert entry["label"] == "initialAmount"
    assert entry["summary"] == initial_amount.summary
    assert entry["description"] == initial_amount.description
    assert entry["package"] == "core"
    assert entry["docs"] == "reference/species/#initialamount"
    assert entry["owner"] == "types/Species"
    assert entry["type"] == {"label": "double", "key": "datatypes/double"}
    assert entry["spec"] == {
        "label": "core 4.6.4",
        "section": "4.6.4",
        "url": glossary.specs["l3v2"].url,
    }
    assert entry["required"] is False
    assert entry["default"] == "set by an initial assignment or a rule"
    expected_rule = {"id": rule.id, "severity": rule.severity, "message": rule.message}
    if rule.section:
        expected_rule["section"] = rule.section
    assert entry["rules"] == [expected_rule]


def test_a_type_lists_its_attributes_and_related_types() -> None:
    """A type entry lists its attributes in the order of the glossary and its related types."""
    glossary = Glossary.from_directory(FIXTURE)
    entry = render_details(glossary)["entries"]["types/Species"]
    assert entry["kind"] == "type"
    assert entry["docs"] == "reference/species/"
    assert entry["attributes"] == [
        "types/Species/initialAmount",
        "types/Species/derivedUnits",
    ]
    assert entry["related"] == ["types/Compartment"]


def test_the_details_of_a_data_type() -> None:
    """A data type entry of the details states its kind and its technical fields."""
    glossary = Glossary.from_directory(FIXTURE)
    datatype = glossary.datatypes["SBOTerm"]
    entry = render_details(glossary)["entries"]["datatypes/SBOTerm"]
    assert entry["kind"] == "datatype"
    assert entry["label"] == "SBOTerm"
    assert entry["summary"] == datatype.summary
    assert entry["description"] == datatype.description
    assert entry["package"] == "core"
    assert entry["docs"] == "reference/datatypes/#sboterm"
    assert entry["values"] == ["entity", "participant role", "modeling framework"]
    # the fixture's SBOTerm cites no specification
    assert "spec" not in entry


def test_the_details_leave_out_what_an_entry_does_not_state() -> None:
    """An entry without a technical detail carries none of those fields."""
    glossary = Glossary.from_directory(FIXTURE)
    entry = render_details(glossary)["entries"]["types/Compartment"]
    for absent in (
        "owner",
        "type",
        "required",
        "default",
        "rules",
        "related",
        "attributes",
        "values",
    ):
        assert absent not in entry
    concept = render_details(glossary)["entries"]["concepts/pk"]
    for absent in ("owner", "type", "required", "default", "rules", "related"):
        assert absent not in concept


def test_a_page_link_becomes_a_glossary_link() -> None:
    """A link to a whole page of the reference becomes the key of its entry."""
    glossary = Glossary.from_directory(FIXTURE)
    entry = render_details(glossary)["entries"]["types/Species"]
    assert "[Compartment](glossary:types/Compartment)" in entry["description"]


def test_an_anchor_link_becomes_the_key_of_the_attribute() -> None:
    """A fragment link to an attribute of the page becomes the key of that attribute."""
    glossary = Glossary.from_directory(FIXTURE)
    entry = render_details(glossary)["entries"]["types/Species"]
    assert (
        "[initial amount](glossary:types/Species/initialAmount)" in entry["description"]
    )


def test_a_link_to_a_page_of_the_site_becomes_absolute(tmp_path: Path) -> None:
    """A link to a page of the site outside the reference becomes its absolute url."""
    glossary = _species_with(
        tmp_path,
        "see [the inspector](../report.md#inspector) and [the home page](../index.md)",
    )
    entry = render_details(glossary)["entries"]["types/Species"]
    assert f"[the inspector]({DOCS_URL}report/#inspector)" in entry["description"]
    assert f"[the home page]({DOCS_URL})" in entry["description"]


def test_a_bare_index_link_becomes_the_directory_url_of_the_reference(
    tmp_path: Path,
) -> None:
    """The index of the reference explains nothing of its own, so it is always absolute.

    `index.md` is not `../index.md`: it is the bare index page of the
    generated reference itself, which `validate_links` accepts both without
    and with an anchor of its own content (here the "Core" section every
    package index carries).
    """
    glossary = _species_with(
        tmp_path,
        "see the [reference](index.md) and its [core section](index.md#core)",
    )
    glossary.validate_links()
    entry = render_details(glossary)["entries"]["types/Species"]
    assert f"[reference]({DOCS_URL}reference/)" in entry["description"]
    assert f"[core section]({DOCS_URL}reference/#core)" in entry["description"]


def test_an_external_link_stays(tmp_path: Path) -> None:
    """A link to an external site is left untouched."""
    glossary = _species_with(tmp_path, "see [SBML](https://sbml.org/) for background")
    entry = render_details(glossary)["entries"]["types/Species"]
    assert "[SBML](https://sbml.org/)" in entry["description"]


def test_every_key_of_the_details_resolves() -> None:
    """Every key the details of the repository glossary reference is itself an entry."""
    root = glossary_module.REPO_ROOT
    glossary = Glossary.from_directory(root / glossary_module.GLOSSARY_DIR)
    entries = render_details(glossary)["entries"]
    problems: list[str] = []
    for key, entry in entries.items():
        candidates: list[str] = []
        if "owner" in entry:
            candidates.append(entry["owner"])
        type_key = entry.get("type", {}).get("key")
        if type_key is not None:
            candidates.append(type_key)
        candidates += entry.get("related", [])
        candidates += entry.get("attributes", [])
        candidates += re.findall(r"\(glossary:([^)]+)\)", entry["description"])
        for candidate in candidates:
            if candidate not in entries:
                problems.append(f"{key}: '{candidate}' has no entry")
    assert problems == []


def test_the_details_are_deterministic() -> None:
    """Two renders of the same glossary produce the same json."""
    glossary = Glossary.from_directory(FIXTURE)
    first = json.dumps(render_details(glossary), indent=2, ensure_ascii=False)
    second = json.dumps(render_details(glossary), indent=2, ensure_ascii=False)
    assert first == second


def test_check_reports_stale_details(tmp_path: Path) -> None:
    """The details json is stale when the glossary changed without regenerating."""
    root = _repository(tmp_path)
    glossary = Glossary.from_directory(root / "glossary")
    write(glossary, root)
    check(root, glossary)
    data = root / "frontend" / "src" / "data" / "glossary-details.json"
    data.write_text(data.read_text(encoding="utf-8").replace("Species", "Spezies"))
    with pytest.raises(
        GlossaryError, match=r"frontend/src/data/glossary-details\.json"
    ):
        check(root, glossary)


def test_the_json_of_the_tooltips_is_unchanged() -> None:
    """`render_json` gains no field now that `render_details` renders the third output."""
    glossary = Glossary.from_directory(FIXTURE)
    data = render_json(glossary)
    assert set(data["types"]["Species"]) == {
        "label",
        "summary",
        "package",
        "page",
        "attributes",
    }


def test_the_docs_url_is_the_url_of_the_site() -> None:
    """`DOCS_URL` is the `site_url` of `zensical.toml`, which the generator cannot read."""
    root = glossary_module.REPO_ROOT
    configuration = tomllib.loads(
        (root / glossary_module.SITE_PATH).read_text(encoding="utf-8")
    )
    assert configuration["project"]["site_url"] == DOCS_URL
