"""The glossary of the report and the generated reference of the documentation.

`glossary/*.toml` in the repository root is the only place where an element
type, an attribute, a link kind or a concept of the report is explained. This
module reads the glossary and writes the two generated artefacts:

* `frontend/src/data/glossary.json`, the labels and the summaries the
  application shows as tooltips,
* `docs/reference/*.md`, the reference pages of the documentation site.

Run `python -m sbml4humans.glossary` after a change of the glossary or of the
report model and commit both outputs. `python -m sbml4humans.glossary --check`
regenerates into a temporary directory and fails when a committed file is
stale, when a type or a field of the report model has no entry, when a link of
a description does not resolve or when a page references a missing image.
"""

import json
import re
import sys
import tomllib
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Self


REPO_ROOT = Path(__file__).resolve().parents[2]

GLOSSARY_DIR = Path("glossary")
JSON_PATH = Path("frontend/src/data/glossary.json")
REFERENCE_DIR = Path("docs/reference")
DOCS_DIR = Path("docs")
SCHEMA_PATH = Path("frontend/src/schema/report.schema.json")
EDGE_KINDS_PATH = Path("frontend/src/data/edgeKinds.ts")

INDEX_PAGE = "index.md"
LINKS_PAGE = "links.md"
CONCEPTS_PAGE = "concepts.md"

# the packages of the report in the order of the reference index
PACKAGES: Mapping[str, str] = {
    "core": "Core",
    "comp": "Hierarchical models (comp)",
    "fbc": "Flux balance constraints (fbc)",
    "distrib": "Distributions (distrib)",
    "report": "Added by the report",
}

# the properties every definition of the report model derived from `SBase` has;
# a definition carrying all of them is an element type of the report
SBASE_PROPERTIES = frozenset(
    {
        "pk",
        "sbmlType",
        "id",
        "metaId",
        "name",
        "sbo",
        "notes",
        "cvterms",
        "history",
        "xml",
    }
)

_ENTRY_KEYS = frozenset(
    {
        "label",
        "summary",
        "description",
        "package",
        "spec",
        "type",
        "related",
        "attributes",
    }
)
_ATTRIBUTE_KEYS = frozenset(
    {"label", "summary", "description", "package", "spec", "type"}
)
_SPEC_KEYS = frozenset({"doc", "section"})
_SPEC_DOCUMENT_KEYS = frozenset({"label", "citation", "url"})
_SECTIONS = ("specs", "types", "links", "concepts")

_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_EXTERNAL = re.compile(r"^(https?:|mailto:|#|/)")
_EDGE_KINDS = re.compile(r"EDGE_KINDS[^=]*=\s*\[(?P<kinds>[^\]]*)\]")


class GlossaryError(Exception):
    """A glossary which is incomplete, inconsistent or not regenerated."""


@dataclass(frozen=True, slots=True)
class SpecDocument:
    """A specification document an entry can cite."""

    key: str
    label: str
    citation: str
    url: str


@dataclass(frozen=True, slots=True)
class SpecRef:
    """The section of a specification document which defines an entry."""

    doc: str
    section: str | None = None


@dataclass(frozen=True, slots=True)
class Entry:
    """One explanation of the glossary: a type, an attribute, a link or a concept."""

    key: str
    label: str
    summary: str
    description: str
    package: str = "core"
    spec: SpecRef | None = None
    type: str | None = None
    related: tuple[str, ...] = ()
    attributes: Mapping[str, Entry] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        """The file name of the reference page of a type, without the suffix."""
        return self.key.lower()

    @property
    def anchor(self) -> str:
        """The anchor of the entry on the page which shows it."""
        return anchor(self.label)


def anchor(label: str) -> str:
    """The anchor of a label on its page: lower case, spaces become dashes.

    It is the anchor the headings of the generated pages get, and the anchor the
    application builds when it links a label into the reference.
    """
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


@dataclass(frozen=True, slots=True)
class Glossary:
    """Every explanation of the report, read from `glossary/*.toml`."""

    specs: Mapping[str, SpecDocument]
    types: Mapping[str, Entry]
    links: Mapping[str, Entry]
    concepts: Mapping[str, Entry]

    @classmethod
    def from_directory(cls, path: Path) -> Self:
        """Read every `*.toml` of the directory into one glossary.

        Args:
            path: the directory holding the glossary files.

        Returns:
            The merged glossary of every file, in the order of the files.

        Raises:
            GlossaryError: when a file is not readable as TOML, when two files
                define the same key, when an entry misses `label`, `summary` or
                `description`, when a `spec` points at an unknown document or
                when a `related` type does not exist.
        """
        files = sorted(path.glob("*.toml"))
        if not files:
            raise GlossaryError(f"no glossary file in {path}")

        data: dict[str, Any] = {}
        owners: dict[str, Path] = {}
        for file in files:
            try:
                content = tomllib.loads(file.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as error:
                raise GlossaryError(f"{file.name}: {error}") from error
            unknown = sorted(set(content) - set(_SECTIONS))
            if unknown:
                raise GlossaryError(
                    f"{file.name}: unknown section {', '.join(unknown)}, "
                    f"expected {', '.join(_SECTIONS)}"
                )
            _merge(data, content, "", owners, file)

        specs = {
            key: _spec_document(key, table, f"specs.{key}", owners)
            for key, table in data.get("specs", {}).items()
        }
        types = {
            key: _entry(key, table, f"types.{key}", owners, nested=False)
            for key, table in data.get("types", {}).items()
        }
        links = {
            key: _entry(key, table, f"links.{key}", owners, nested=True)
            for key, table in data.get("links", {}).items()
        }
        concepts = {
            key: _entry(key, table, f"concepts.{key}", owners, nested=True)
            for key, table in data.get("concepts", {}).items()
        }
        glossary = cls(specs=specs, types=types, links=links, concepts=concepts)
        glossary._validate_references(owners)
        return glossary

    def entries(self) -> Iterator[tuple[str, Entry]]:
        """Every entry of the glossary with its dotted key, attributes included."""
        for section, entries in (
            ("types", self.types),
            ("links", self.links),
            ("concepts", self.concepts),
        ):
            for key, entry in entries.items():
                yield f"{section}.{key}", entry
                for name, attribute in entry.attributes.items():
                    yield f"{section}.{key}.attributes.{name}", attribute

    def pages(self) -> set[str]:
        """The file names of the generated reference pages."""
        return {INDEX_PAGE, LINKS_PAGE, CONCEPTS_PAGE} | {
            f"{entry.slug}.md" for entry in self.types.values()
        }

    def validate_links(self, root: Path | None = None) -> None:
        """Check that every link of a description and every image resolves.

        Args:
            root: the repository root. When it is given, every image of every
                page under `docs/` has to exist as well.

        Raises:
            GlossaryError: when a `[text](target.md)` link of a description does
                not name a generated page, or when an image is missing.
        """
        pages = self.pages()
        problems: list[str] = []
        for key, entry in self.entries():
            for text, target in _LINK.findall(entry.description):
                if _EXTERNAL.match(target):
                    continue
                page = target.split("#", 1)[0]
                if page not in pages:
                    problems.append(
                        f"{key}: the link [{text}]({target}) does not resolve to a "
                        f"reference page"
                    )
        if root is not None:
            problems.extend(_missing_images(root))
        if problems:
            raise GlossaryError("\n".join(["broken links:", *problems]))

    def validate_coverage(self, root: Path) -> None:
        """Check that the glossary explains everything the report shows.

        Every definition of `report.schema.json` derived from `SBase` needs a
        type entry and every property of it needs an attribute entry, either on
        the type itself, on the shared `SBase` attributes or as a concept of the
        report. A property which every type carries is explained once, as a
        shared attribute or as a concept. Every kind of `edgeKinds.ts` needs a
        link entry.

        Args:
            root: the repository root.

        Raises:
            GlossaryError: with the list of everything which has no entry.
        """
        missing: list[str] = []
        schema = json.loads((root / SCHEMA_PATH).read_text(encoding="utf-8"))
        shared = self.types.get("SBase")
        shared_attributes = shared.attributes if shared else {}
        definitions = {
            name: definition.get("properties", {})
            for name, definition in sorted(schema.get("$defs", {}).items())
            if set(definition.get("properties", {})) >= SBASE_PROPERTIES
        }
        common = set.intersection(*(set(p) for p in definitions.values()))
        for property_name in sorted(common):
            if property_name in shared_attributes or property_name in self.concepts:
                continue
            missing.append(f"the shared field {property_name} has no entry")
        for name, properties in definitions.items():
            entry = self.types.get(name)
            if entry is None:
                missing.append(f"the type {name} of the report has no entry")
                continue
            for property_name in properties:
                if (
                    property_name in common
                    or property_name in entry.attributes
                    or property_name in shared_attributes
                    or property_name in self.concepts
                ):
                    continue
                missing.append(f"the field {name}.{property_name} has no entry")
        for kind in _edge_kinds(root / EDGE_KINDS_PATH):
            if kind not in self.links:
                missing.append(f"the link kind {kind} has no entry")
        if missing:
            raise GlossaryError(
                "\n".join(["the glossary does not cover the report:", *missing])
            )

    def _validate_references(self, owners: Mapping[str, Path]) -> None:
        """Check that every `spec` and every `related` entry exists."""
        for key, entry in self.entries():
            if entry.spec is not None and entry.spec.doc not in self.specs:
                raise GlossaryError(
                    f"{_where(key, owners)}: the spec document '{entry.spec.doc}' is "
                    f"not defined, known documents are "
                    f"{', '.join(sorted(self.specs)) or 'none'}"
                )
            for name in entry.related:
                if name not in self.types:
                    raise GlossaryError(
                        f"{_where(key, owners)}: the related type '{name}' has no entry"
                    )


def _merge(
    target: dict[str, Any],
    source: Mapping[str, Any],
    prefix: str,
    owners: dict[str, Path],
    file: Path,
) -> None:
    """Merge the tables of one glossary file into the merged glossary.

    Two files may contribute different entries to the same table, for example
    the attributes of a package added to a core type, but no key is defined
    twice.
    """
    for key, value in source.items():
        path = f"{prefix}{key}"
        existing = target.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            _merge(existing, value, f"{path}.", owners, file)
        elif key in target:
            raise GlossaryError(
                f"{file.name}: '{path}' is already defined in {owners[path].name}"
            )
        else:
            target[key] = value
            _own(value, path, owners, file)


def _own(value: Any, path: str, owners: dict[str, Path], file: Path) -> None:
    """Record the file which defines a key and every key below it."""
    owners[path] = file
    if isinstance(value, dict):
        for key, item in value.items():
            _own(item, f"{path}.{key}", owners, file)


def _where(path: str, owners: Mapping[str, Path]) -> str:
    """The file and the key of an entry, for an error message."""
    file = owners.get(path)
    return f"{file.name}: {path}" if file else path


def _table(path: str, value: Any, owners: Mapping[str, Path]) -> Mapping[str, Any]:
    """The value of an entry as a table."""
    if not isinstance(value, dict):
        raise GlossaryError(f"{_where(path, owners)}: expected a table")
    return value


def _string(
    path: str, table: Mapping[str, Any], key: str, owners: Mapping[str, Path]
) -> str:
    """One required string of an entry."""
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GlossaryError(f"{_where(path, owners)}: '{key}' is missing")
    return value.strip()


def _known_keys(
    path: str,
    table: Mapping[str, Any],
    allowed: frozenset[str],
    owners: Mapping[str, Path],
) -> None:
    """Reject a key which the format does not define, most likely a typo."""
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise GlossaryError(
            f"{_where(path, owners)}: unknown key {', '.join(unknown)}, "
            f"expected {', '.join(sorted(allowed))}"
        )


def _spec_document(
    key: str, value: Any, path: str, owners: Mapping[str, Path]
) -> SpecDocument:
    """One document of the `specs` table."""
    table = _table(path, value, owners)
    _known_keys(path, table, _SPEC_DOCUMENT_KEYS, owners)
    return SpecDocument(
        key=key,
        label=_string(path, table, "label", owners),
        citation=_string(path, table, "citation", owners),
        url=_string(path, table, "url", owners),
    )


def _spec_ref(value: Any, path: str, owners: Mapping[str, Path]) -> SpecRef:
    """The `spec` of an entry."""
    table = _table(path, value, owners)
    _known_keys(path, table, _SPEC_KEYS, owners)
    section = table.get("section")
    if section is not None and not isinstance(section, str):
        raise GlossaryError(f"{_where(path, owners)}: 'section' is not a string")
    return SpecRef(doc=_string(path, table, "doc", owners), section=section)


def _entry(
    key: str, value: Any, path: str, owners: Mapping[str, Path], *, nested: bool
) -> Entry:
    """One entry of the glossary, with its attributes when it is a type.

    Args:
        key: the key of the entry, the name of the type or of the field.
        value: the table of the entry.
        path: the dotted path of the entry, for the error messages.
        owners: the file every key was read from.
        nested: an attribute, a link kind or a concept, which has neither
            attributes nor related types.
    """
    table = _table(path, value, owners)
    _known_keys(path, table, _ATTRIBUTE_KEYS if nested else _ENTRY_KEYS, owners)
    summary = _string(path, table, "summary", owners)
    if summary.endswith("."):
        raise GlossaryError(
            f"{_where(path, owners)}: the summary ends with a period, it is one "
            f"sentence shown as a tooltip"
        )
    related = table.get("related", [])
    if not isinstance(related, list) or not all(
        isinstance(name, str) for name in related
    ):
        raise GlossaryError(f"{_where(path, owners)}: 'related' is not a list of names")
    spec = table.get("spec")
    attributes = table.get("attributes", {})
    return Entry(
        key=key,
        label=_string(path, table, "label", owners),
        summary=summary,
        description=_string(path, table, "description", owners),
        package=str(table.get("package", "core")),
        spec=None if spec is None else _spec_ref(spec, f"{path}.spec", owners),
        type=table.get("type"),
        related=tuple(related),
        attributes={
            name: _entry(
                name, attribute, f"{path}.attributes.{name}", owners, nested=True
            )
            for name, attribute in _table(
                f"{path}.attributes", attributes, owners
            ).items()
        },
    )


def _edge_kinds(path: Path) -> list[str]:
    """The `EDGE_KINDS` array of the frontend."""
    match = _EDGE_KINDS.search(path.read_text(encoding="utf-8"))
    if match is None:
        raise GlossaryError(f"{path}: no EDGE_KINDS array")
    return re.findall(r'"([^"]+)"', match.group("kinds"))


def _missing_images(root: Path) -> list[str]:
    """Every image a page under `docs/` references and which does not exist."""
    problems: list[str] = []
    for page in sorted((root / DOCS_DIR).rglob("*.md")):
        for text, target in _IMAGE.findall(page.read_text(encoding="utf-8")):
            if _EXTERNAL.match(target):
                continue
            image = (page.parent / target.split("#", 1)[0]).resolve()
            if not image.is_file():
                relative = page.relative_to(root)
                problems.append(f"{relative}: the image ![{text}]({target}) is missing")
    return problems


def _sentence(summary: str) -> str:
    """A summary as a sentence, for the lead paragraph of a page."""
    return f"{summary[:1].upper()}{summary[1:]}."


def _cell(text: str | None) -> str:
    """One cell of a markdown table, a dash when there is nothing to show."""
    return (text or "-").replace("|", "\\|")


def _spec_link(glossary: Glossary, spec: SpecRef | None) -> str:
    """The specification section of an entry as a link into the document."""
    if spec is None:
        return "-"
    document = glossary.specs[spec.doc]
    label = f"Section {spec.section}" if spec.section else document.label
    return f"[{label}]({document.url})"


def _table_rows(header: Iterable[str], rows: Iterable[Iterable[str]]) -> list[str]:
    """A markdown table, empty when it has no row."""
    columns = list(header)
    body = [f"| {' | '.join(row)} |" for row in rows]
    if not body:
        return []
    return [
        f"| {' | '.join(columns)} |",
        f"| {' | '.join('---' for _ in columns)} |",
        *body,
    ]


def _attribute_rows(
    glossary: Glossary, attributes: Iterable[Entry], *, with_spec: bool
) -> list[list[str]]:
    """One row per attribute.

    A markdown table has no place for the id of a row, so the anchor of an
    attribute, which the application links to, opens its meaning.
    """
    rows = []
    for attribute in attributes:
        row = [
            _cell(attribute.label),
            f"`{attribute.type}`" if attribute.type else "-",
            f'<span id="{attribute.anchor}"></span>{_cell(attribute.summary)}',
        ]
        if with_spec:
            row.append(_spec_link(glossary, attribute.spec))
        rows.append(row)
    return rows


def render_type_page(glossary: Glossary, entry: Entry) -> str:
    """The reference page of one element type.

    Args:
        glossary: the glossary the entry belongs to.
        entry: the type entry.

    Returns:
        The markdown of `docs/reference/<slug>.md`.
    """
    lines = [
        f"# {entry.label}",
        "",
        _sentence(entry.summary),
        "",
        entry.description,
        "",
    ]

    attributes = [a for a in entry.attributes.values() if a.package != "report"]
    rows = _attribute_rows(glossary, attributes, with_spec=True)
    if rows:
        lines += ["## Attributes", ""]
        lines += _table_rows(["attribute", "type", "meaning", "specification"], rows)
        lines += [""]
        if entry.key != "SBase" and "SBase" in glossary.types:
            lines += [
                "Every element of a model also carries the "
                "[common attributes](sbase.md) of `SBase`.",
                "",
            ]

    report_fields = [a for a in entry.attributes.values() if a.package == "report"]
    rows = _attribute_rows(glossary, report_fields, with_spec=False)
    if rows:
        lines += ["## In the report", ""]
        lines += _table_rows(["field", "type", "meaning"], rows)
        lines += [""]

    if entry.related:
        lines += ["## Related elements", ""]
        for name in entry.related:
            related = glossary.types[name]
            lines.append(f"- [{related.label}]({related.slug}.md): {related.summary}")
        lines += [""]

    if entry.spec is not None:
        document = glossary.specs[entry.spec.doc]
        section = f", Section {entry.spec.section}" if entry.spec.section else ""
        lines += [
            "## Specification",
            "",
            f"[{document.label}]({document.url}){section} ({document.citation}).",
            "",
        ]
    return "\n".join(lines).rstrip("\n") + "\n"


def render_index_page(glossary: Glossary) -> str:
    """The index of the reference, the types grouped by package."""
    lines = [
        "# Reference",
        "",
        "Every element type a report shows, the attributes of the elements and the "
        "fields the report adds. The pages are generated from the glossary of the "
        "repository, which is also the source of the tooltips of the application.",
        "",
        f"The [link kinds]({LINKS_PAGE}) explain how the elements of a report "
        f"reference each other, the [report concepts]({CONCEPTS_PAGE}) explain what "
        f"the report computes on top of the model.",
        "",
    ]
    for package, heading in PACKAGES.items():
        entries = [
            entry for entry in glossary.types.values() if entry.package == package
        ]
        if not entries:
            continue
        rows = [
            [f"[{entry.label}]({entry.slug}.md)", _cell(entry.summary)]
            for entry in entries
        ]
        lines += [f"## {heading}", ""]
        lines += _table_rows(["element", "meaning"], rows)
        lines += [""]
    return "\n".join(lines).rstrip("\n") + "\n"


def _render_entries_page(
    title: str, lead: str, entries: Iterable[Entry], glossary: Glossary
) -> str:
    """A page with one section per entry, used for the links and the concepts."""
    lines = [f"# {title}", "", lead, ""]
    for entry in entries:
        lines += [
            f"## {entry.label}",
            "",
            _sentence(entry.summary),
            "",
            entry.description,
        ]
        if entry.spec is not None:
            document = glossary.specs[entry.spec.doc]
            section = f", Section {entry.spec.section}" if entry.spec.section else ""
            lines += ["", f"[{document.label}]({document.url}){section}."]
        lines += [""]
    return "\n".join(lines).rstrip("\n") + "\n"


def render_links_page(glossary: Glossary) -> str:
    """The page of the link kinds of the report."""
    return _render_entries_page(
        "Link kinds",
        "An element of a report references other elements, and is referenced by "
        'others. The inspector groups both directions by kind under "References" '
        'and "Referenced by", the tables link the referenced element directly.',
        glossary.links.values(),
        glossary,
    )


def render_concepts_page(glossary: Glossary) -> str:
    """The page of the concepts the report adds to a model."""
    return _render_entries_page(
        "Report concepts",
        "A report shows more than the model file contains: it resolves references, "
        "derives units, renders the math and names every element. These are the "
        "fields the report computes.",
        glossary.concepts.values(),
        glossary,
    )


def render_json(glossary: Glossary) -> dict[str, Any]:
    """The entries the application reads, without the descriptions.

    Args:
        glossary: the glossary to render.

    Returns:
        The content of `frontend/src/data/glossary.json`, sorted by key. The
        `page` of an entry is the path of its reference page below the url of
        the documentation site.
    """
    return {
        "types": {
            name: {
                "label": entry.label,
                "summary": entry.summary,
                "package": entry.package,
                "page": f"{REFERENCE_DIR.name}/{entry.slug}/",
                "attributes": {
                    field_name: {"label": attribute.label, "summary": attribute.summary}
                    for field_name, attribute in sorted(entry.attributes.items())
                },
            }
            for name, entry in sorted(glossary.types.items())
        },
        "links": _render_json_entries(glossary.links, LINKS_PAGE),
        "concepts": _render_json_entries(glossary.concepts, CONCEPTS_PAGE),
    }


def _render_json_entries(entries: Mapping[str, Entry], page: str) -> dict[str, Any]:
    """The link kinds or the concepts of the json, with the anchor of their page."""
    return {
        key: {
            "label": entry.label,
            "summary": entry.summary,
            "page": f"{REFERENCE_DIR.name}/{Path(page).stem}/#{entry.anchor}",
        }
        for key, entry in sorted(entries.items())
    }


def _files(glossary: Glossary) -> dict[Path, str]:
    """Every generated file with its content, relative to the repository root."""
    files: dict[Path, str] = {
        JSON_PATH: json.dumps(render_json(glossary), indent=2, ensure_ascii=False)
        + "\n",
        REFERENCE_DIR / INDEX_PAGE: render_index_page(glossary),
        REFERENCE_DIR / LINKS_PAGE: render_links_page(glossary),
        REFERENCE_DIR / CONCEPTS_PAGE: render_concepts_page(glossary),
    }
    for entry in glossary.types.values():
        files[REFERENCE_DIR / f"{entry.slug}.md"] = render_type_page(glossary, entry)
    return files


def write(glossary: Glossary, root: Path) -> list[Path]:
    """Write the json and the reference pages below the root.

    Args:
        glossary: the glossary to render.
        root: the repository root, or a temporary directory for the check.

    Returns:
        The written files, relative to the root.
    """
    files = _files(glossary)
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return sorted(files)


def check(root: Path, glossary: Glossary | None = None) -> None:
    """Check that the committed files are the files the glossary generates.

    Args:
        root: the repository root.
        glossary: the glossary, read from `root` when it is not given.

    Raises:
        GlossaryError: with the list of the files which are not current.
    """
    glossary = glossary or Glossary.from_directory(root / GLOSSARY_DIR)
    files = _files(glossary)
    with TemporaryDirectory() as directory:
        write(glossary, Path(directory))
        stale = [
            str(relative)
            for relative in sorted(files)
            if not (root / relative).is_file()
            or (root / relative).read_text(encoding="utf-8")
            != (Path(directory) / relative).read_text(encoding="utf-8")
        ]
    generated = {root / relative for relative in files}
    stale += [
        str(page.relative_to(root))
        for page in sorted((root / REFERENCE_DIR).glob("*.md"))
        if page not in generated
    ]
    if stale:
        raise GlossaryError(
            "\n".join(
                [
                    "the generated files are not current, run "
                    "`uv run python -m sbml4humans.glossary`:",
                    *stale,
                ]
            )
        )


def main(argv: list[str]) -> int:
    """Write the generated files, or check that they are current.

    Args:
        argv: the command line, `--check` checks instead of writing.

    Returns:
        The exit code, 1 when a file is stale or an explanation is missing.
    """
    root = REPO_ROOT
    try:
        glossary = Glossary.from_directory(root / GLOSSARY_DIR)
    except GlossaryError as error:
        print(error, file=sys.stderr)
        return 1

    if "--check" in argv[1:]:
        checks: tuple[Callable[[], None], ...] = (
            lambda: check(root, glossary),
            lambda: glossary.validate_coverage(root),
            lambda: glossary.validate_links(root),
        )
        problems: list[str] = []
        for validate in checks:
            try:
                validate()
            except GlossaryError as error:
                problems.append(str(error))
        if problems:
            print("\n\n".join(problems), file=sys.stderr)
            return 1
        print("the glossary covers the report and the generated files are current")
        return 0

    for relative in write(glossary, root):
        print(f"written {relative}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
