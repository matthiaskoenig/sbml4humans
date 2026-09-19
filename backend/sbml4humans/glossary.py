"""The glossary of the report and the generated reference of the documentation.

`glossary/*.toml` in the repository root is the only place where an element
type, an attribute, a link kind or a concept of the report is explained. This
module reads the glossary and writes the three generated artefacts:

* `frontend/src/data/glossary.json`, the labels and the summaries the
  application shows as tooltips,
* `frontend/src/data/glossary-details.json`, the description and the
  technical details of every entry, for the help dialog of the report,
* `docs/reference/*.md`, the reference pages of the documentation site.

Run `uv run python -m sbml4humans.glossary` from `backend/` after a change of
the glossary or of the report model and commit both outputs.
`uv run python -m sbml4humans.glossary --check` regenerates into a temporary
directory and fails when a committed file is stale, when a type or a field of
the report model has no entry, when a type or an attribute entry of the
glossary is not a type or a field of the report, when a type or an attribute
of a specification is not labelled by its name there, when an attribute the
report adds states `required` or cites a validation rule which does not
exist or belongs to a foreign package, when a `type` resolves to neither a
data type nor a type of the glossary or a data type nothing uses, when an
attribute of a specification does not state whether it is required, when a
link of a description does not resolve to a page or to an anchor of one,
when a page references a missing image or when the navigation of the site
does not list a generated page.
"""

import json
import re
import sys
import tomllib
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, Self

from sbml4humans.glossaryrules import Rule, UnknownRuleError, resolve_rule


REPO_ROOT = Path(__file__).resolve().parents[2]

GLOSSARY_DIR = Path("glossary")
JSON_PATH = Path("frontend/src/data/glossary.json")
DETAILS_PATH = Path("frontend/src/data/glossary-details.json")
REFERENCE_DIR = Path("docs/reference")
DOCS_DIR = Path("docs")
SCHEMA_PATH = Path("frontend/src/schema/report.schema.json")
EDGE_KINDS_PATH = Path("frontend/src/data/edgeKinds.ts")
SITE_PATH = Path("zensical.toml")

# the `site_url` of `zensical.toml`; `render_details` rewrites a link of a
# description into an absolute url of the site and cannot read the
# configuration itself without the repository root, so it is a constant,
# checked against `zensical.toml` by a test of the repository
DOCS_URL = "https://matthiaskoenig.github.io/sbml4humans/"

INDEX_PAGE = "index.md"
LINKS_PAGE = "links.md"
CONCEPTS_PAGE = "concepts.md"
# the page of the data types, rendered by a later change; the details already
# need its name and the anchors of its entries to rewrite a link into one
DATATYPES_PAGE = "datatypes.md"

# the headings of a generated type page below its title; their anchors are
# taken before the attributes of the page get theirs
PAGE_HEADINGS = (
    "Attributes",
    "In the report",
    "Validation rules",
    "Related elements",
    "Specification",
)

# the packages of the report in the order of the reference index
PACKAGES: Mapping[str, str] = {
    "core": "Core",
    "comp": "Hierarchical models (comp)",
    "fbc": "Flux balance constraints (fbc)",
    "qual": "Qualitative models (qual)",
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

# the objects an element of the report carries which the report shows as one
# value: a rendered formula, the history block, a parameter with its value.
# The entry of the field explains them. Every other object an element carries
# inline, the comp and the fbc extensions and the trigger of an event, is shown
# field by field, so every one of its fields needs an entry `<field>.<name>`.
SINGLE_VALUE_DEFINITIONS = frozenset({"ConversionFactor", "Math", "ModelHistory"})

# the type entries which are not an element type of the report: the shared
# attributes of `SBase` and the three packages, which have a page of their own
NON_ELEMENT_TYPES = frozenset({"SBase", "comp", "fbc", "qual", "distrib"})

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
        "rules",
    }
)
_ATTRIBUTE_KEYS = frozenset(
    {
        "label",
        "summary",
        "description",
        "package",
        "spec",
        "type",
        "required",
        "default",
        "rules",
    }
)
_DATATYPE_KEYS = frozenset(
    {"label", "summary", "description", "package", "spec", "related", "values"}
)
_SPEC_KEYS = frozenset({"doc", "section"})
_SPEC_DOCUMENT_KEYS = frozenset({"label", "short", "citation", "url"})
_SECTIONS = ("specs", "types", "links", "concepts", "datatypes")

_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_EXTERNAL = re.compile(r"^(https?:|mailto:|#|/)")
_EDGE_KINDS = re.compile(r"EDGE_KINDS[^=]*=\s*\[(?P<kinds>[^\]]*)\]")
_HEADING = re.compile(r"^#{1,6}\s+(?P<text>.*?)\s*(?:\{#(?P<id>[^}\s]+)\})?\s*$")
_ELEMENT_ID = re.compile(r'\bid="([^"]+)"')
_FENCE = re.compile(r"^\s*(```|~~~)")


class GlossaryError(Exception):
    """A glossary which is incomplete, inconsistent or not regenerated."""


@dataclass(frozen=True, slots=True)
class SpecDocument:
    """A specification document an entry can cite."""

    key: str
    label: str
    citation: str
    url: str
    short: str


@dataclass(frozen=True, slots=True)
class SpecRef:
    """The section of a specification document which defines an entry."""

    doc: str
    section: str | None = None


@dataclass(frozen=True, slots=True)
class Entry:
    """One explanation of the glossary: a type, an attribute, a link, a concept or a data type."""

    key: str
    label: str
    summary: str
    description: str
    package: str = "core"
    spec: SpecRef | None = None
    type: str | None = None
    related: tuple[str, ...] = ()
    attributes: Mapping[str, Entry] = field(default_factory=dict)
    required: bool | None = None
    default: str | None = None
    rules: tuple[int, ...] = ()
    values: tuple[str, ...] = ()

    @property
    def slug(self) -> str:
        """The file name of the reference page of a type, without the suffix."""
        return self.key.lower()


def anchor(label: str) -> str:
    """The anchor of a label on its page: lower case, spaces become dashes.

    It is the anchor the headings of the generated pages get, and the anchor the
    links of the site point at.
    """
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _entry_anchors(entries: Iterable[Entry], reserved: Iterable[str]) -> dict[str, str]:
    """The anchor of every entry of one page, by key and unique within the page.

    The first entry with a label keeps the anchor of the label, every further
    entry with the same label gets a numbered suffix: a reaction explains both
    the kinetic law of the model and the formula the report renders from it,
    both labelled "kinetic law", and the two blocks need two ids.

    Args:
        entries: the entries of the page, in the order they are rendered in.
        reserved: the anchors the page already carries, its headings.
    """
    used = set(reserved)
    anchors: dict[str, str] = {}
    for entry in entries:
        base = anchor(entry.label)
        candidate, index = base, 1
        while candidate in used:
            index += 1
            candidate = f"{base}-{index}"
        used.add(candidate)
        anchors[entry.key] = candidate
    return anchors


def _anchors_of(page: str) -> list[str]:
    """Every anchor a markdown page offers, in the order of the page.

    A heading carries the anchor of its text, or the identifier an attribute
    list `{#id}` gives it, and an element written as HTML carries the id of its
    `id` attribute. The anchors are not made unique here, so that a page which
    offers one of them twice stays visible to the test which forbids it.
    """
    anchors: list[str] = []
    fenced = False
    for line in page.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = _HEADING.match(line) if line.startswith("#") else None
        if heading is not None:
            anchors.append(heading.group("id") or anchor(heading.group("text")))
        anchors.extend(_ELEMENT_ID.findall(line))
    return anchors


@dataclass(frozen=True, slots=True)
class Glossary:
    """Every explanation of the report, read from `glossary/*.toml`."""

    specs: Mapping[str, SpecDocument]
    types: Mapping[str, Entry]
    links: Mapping[str, Entry]
    concepts: Mapping[str, Entry]
    datatypes: Mapping[str, Entry]
    # the file every key was read from, for the messages of the checks
    owners: Mapping[str, Path] = field(default_factory=dict)

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
            key: _entry(key, table, f"types.{key}", owners, kind="type")
            for key, table in data.get("types", {}).items()
        }
        links = {
            key: _entry(key, table, f"links.{key}", owners, kind="nested")
            for key, table in data.get("links", {}).items()
        }
        concepts = {
            key: _entry(key, table, f"concepts.{key}", owners, kind="nested")
            for key, table in data.get("concepts", {}).items()
        }
        datatypes = {
            key: _entry(key, table, f"datatypes.{key}", owners, kind="datatype")
            for key, table in data.get("datatypes", {}).items()
        }
        glossary = cls(
            specs=specs,
            types=types,
            links=links,
            concepts=concepts,
            datatypes=datatypes,
            owners=owners,
        )
        glossary._validate_references()
        return glossary

    def entries(self) -> Iterator[tuple[str, Entry]]:
        """Every entry of the glossary with its dotted key, attributes included."""
        for section, entries in (
            ("types", self.types),
            ("links", self.links),
            ("concepts", self.concepts),
            ("datatypes", self.datatypes),
        ):
            for key, entry in entries.items():
                yield f"{section}.{key}", entry
                for name, attribute in entry.attributes.items():
                    yield f"{section}.{key}.attributes.{name}", attribute

    def pages(self) -> set[str]:
        """The file names of the generated reference pages."""
        return {INDEX_PAGE, LINKS_PAGE, CONCEPTS_PAGE, DATATYPES_PAGE} | {
            f"{entry.slug}.md" for entry in self.types.values()
        }

    def page_of(self, key: str) -> str:
        """The generated page an entry is rendered on.

        Args:
            key: the dotted key of the entry, as `entries` yields it.

        Returns:
            The file name of the page, for example `species.md`.
        """
        section, _, rest = key.partition(".")
        if section == "types":
            return f"{self.types[rest.split('.', 1)[0]].slug}.md"
        if section == "links":
            return LINKS_PAGE
        if section == "concepts":
            return CONCEPTS_PAGE
        return DATATYPES_PAGE

    def validate_links(self, root: Path | None = None) -> None:
        """Check that every link of a description and every image resolves.

        A link to a reference page names a page the glossary generates, a link
        which starts with `../` a page of the documentation outside the
        reference, and a fragment an anchor of the page it points into, which is
        the page the entry itself is rendered on when the target is a bare
        `#anchor`.

        Args:
            root: the repository root. When it is given, a page outside the
                reference and every image of every page under `docs/` have to
                exist as well.

        Raises:
            GlossaryError: when a `[text](target.md)` link of a description does
                not name a generated page or an anchor of one, or when an image
                is missing.
        """
        anchors = {
            name: set(_anchors_of(page))
            for name, page in _reference_pages(self).items()
        }
        problems: list[str] = []
        for key, entry in self.entries():
            for text, target in _LINK.findall(entry.description):
                problem = _link_problem(target, anchors, self.page_of(key), root)
                if problem is not None:
                    problems.append(
                        f"{key}: the link [{text}]({target}) {problem}",
                    )
        if root is not None:
            problems.extend(_missing_images(root))
        if problems:
            raise GlossaryError("\n".join(["broken links:", *problems]))

    def validate_navigation(self, root: Path) -> None:
        """Check that the navigation of the site lists every generated page.

        A type which is added to the glossary generates a page, which zensical
        builds and finds by its links, but which stays out of the navigation
        until `zensical.toml` names it.

        Args:
            root: the repository root.

        Raises:
            GlossaryError: with the pages the navigation does not list, or when
                the configuration of the site cannot be read.
        """
        try:
            configuration = tomllib.loads(_read(root / SITE_PATH))
        except tomllib.TOMLDecodeError as error:
            raise GlossaryError(f"{SITE_PATH}: {error}") from error
        project = configuration.get("project", {})
        listed = set(_navigation_pages(project.get("nav", [])))
        missing = [
            path
            for name in sorted(self.pages())
            if (path := f"{REFERENCE_DIR.name}/{name}") not in listed
        ]
        if missing:
            raise GlossaryError(
                "\n".join(
                    [
                        f"the navigation of {SITE_PATH} does not list every "
                        f"generated page:",
                        *missing,
                    ]
                )
            )

    def validate_coverage(self, root: Path) -> None:
        """Check that the glossary explains everything the report shows.

        Every definition of `report.schema.json` derived from `SBase` needs a
        type entry and every property of it needs an attribute entry, either on
        the type itself, on the shared `SBase` attributes or as a concept of the
        report. A property which every type carries is explained once, as a
        shared attribute or as a concept. A property which holds an object the
        report shows field by field, the comp and the fbc extensions or the
        trigger of an event, needs an entry `<property>.<field>` for every one
        of its fields. Every kind of `edgeKinds.ts` needs a link entry, and in
        the other direction every type entry of the glossary is a type of the
        report, except the shared attributes and the three packages, and every
        attribute entry of a type names a field of that type, except a field of
        the `report` package, which the application derives and which the report
        model therefore does not carry.

        Args:
            root: the repository root.

        Raises:
            GlossaryError: with the list of everything which has no entry or
                which the report does not have, when no definition of the report
                model carries the shared properties, or when the report model or
                the edge kinds cannot be read.
        """
        missing: list[str] = []
        schema = json.loads(_read(root / SCHEMA_PATH))
        defs: Mapping[str, Any] = schema.get("$defs", {})
        shared = self.types.get("SBase")
        shared_attributes = shared.attributes if shared else {}
        definitions = {
            name: definition.get("properties", {})
            for name, definition in sorted(defs.items())
            if set(definition.get("properties", {})) >= SBASE_PROPERTIES
        }
        if not definitions:
            raise GlossaryError(
                f"no definition of {SCHEMA_PATH} carries the properties of an SBase, "
                f"so the report model cannot be read: update SBASE_PROPERTIES "
                f"({', '.join(sorted(SBASE_PROPERTIES))}) to the fields of `SBase` "
                f"in model.py"
            )
        common = set.intersection(*(set(p) for p in definitions.values()))
        # the shared properties are the same in every definition
        shared_properties: Mapping[str, Any] = next(iter(definitions.values()))
        known_fields = {
            name: _known_fields(defs, properties)
            for name, properties in definitions.items()
        }
        known_fields["SBase"] = _known_fields(
            defs, {name: shared_properties[name] for name in common}
        )

        def covered(*names: str) -> bool:
            """Whether one of the names is explained somewhere in the glossary."""
            return any(
                name in shared_attributes or name in self.concepts for name in names
            )

        for property_name in sorted(common):
            for field_name in _fields(defs, shared_properties, property_name):
                if not covered(field_name):
                    missing.append(f"the shared field {field_name} has no entry")
        for name, properties in definitions.items():
            entry = self.types.get(name)
            if entry is None:
                missing.append(f"the type {name} of the report has no entry")
                continue
            for property_name in properties:
                if property_name in common:
                    continue
                for field_name in _fields(defs, properties, property_name):
                    if field_name not in entry.attributes and not covered(field_name):
                        missing.append(f"the field {name}.{field_name} has no entry")
        for key, entry in self.types.items():
            if key not in definitions and key not in NON_ELEMENT_TYPES:
                missing.append(f"the type {key} is not a type of the report")
            fields = known_fields.get(key)
            if fields is None:
                continue
            for name, attribute in entry.attributes.items():
                if name not in fields and attribute.package != "report":
                    where = _where(f"types.{key}.attributes.{name}", self.owners)
                    missing.append(f"{where} is not a field of {key} in the report")
        for kind in _edge_kinds(root / EDGE_KINDS_PATH):
            if kind not in self.links:
                missing.append(f"the link kind {kind} has no entry")
        if missing:
            raise GlossaryError(
                "\n".join(["the glossary does not cover the report:", *missing])
            )

    def validate_labels(self) -> None:
        """Check that what the specification names is labelled by that name.

        A type is labelled by the name of its class, `FunctionDefinition` and not
        "Function definition", and an attribute which cites a specification by
        the name it has there, `initialConcentration`, or `fbc:charge` for an
        attribute a package adds to a type of the core: a name is one word. An
        attribute the report adds cites no specification and is labelled in plain
        words, "derived units", so that a reader tells the two apart. A link kind
        is labelled by its key, which is the name of the attribute that refers.

        Raises:
            GlossaryError: with every label which is not such a name.
        """
        problems: list[str] = []
        for key, entry in self.types.items():
            if key not in PACKAGES and entry.label != key:
                problems.append(
                    f"{_where(f'types.{key}', self.owners)}: the type is labelled "
                    f"'{entry.label}', not by its name '{key}'"
                )
            problems += [
                f"{_where(f'types.{key}.attributes.{name}', self.owners)}: the "
                f"attribute cites a specification and is labelled '{attribute.label}',"
                f" which is not a name of a specification"
                for name, attribute in entry.attributes.items()
                if attribute.spec is not None
                and not re.fullmatch(r"([a-z]+:)?[A-Za-z][A-Za-z0-9]*", attribute.label)
            ]
        # a link kind is the attribute which makes the reference, under the same name
        problems += [
            f"{_where(f'links.{key}', self.owners)}: the link kind is labelled "
            f"'{entry.label}', not by its name '{key}'"
            for key, entry in self.links.items()
            if entry.label != key
        ]
        if problems:
            raise GlossaryError("\n".join(["labels:", *problems]))

    def type_key(self, name: str) -> str | None:
        """The entry a `type` value of an attribute names, for a link into its page.

        Args:
            name: the `type` of an attribute, as written; a list notation
                `Foo[]` is stripped to `Foo` before the lookup.

        Returns:
            `"datatypes/<name>"` when the stripped name is a data type,
            `"types/<name>"` when it is a type of the glossary, `None` when it
            is neither.
        """
        stripped = name.removesuffix("[]")
        if stripped in self.datatypes:
            return f"datatypes/{stripped}"
        if stripped in self.types:
            return f"types/{stripped}"
        return None

    def resolved_rules(self, entry: Entry) -> list[Rule]:
        """The validation rules an entry cites, resolved with libsbml.

        Args:
            entry: a type or an attribute of the glossary.

        Returns:
            The `Rule` of every number of `entry.rules`, in the order they are
            cited.

        Raises:
            UnknownRuleError: a number of `entry.rules` is not a validation
                rule of libsbml.
        """
        return [resolve_rule(code) for code in entry.rules]

    def validate_technical(self) -> None:
        """Check the technical details an entry states about itself.

        An attribute which the report adds, rather than one of the
        specification, cites no `spec` and therefore cannot be `required` by
        one. A rule cited by `rules` has to resolve with libsbml and has to
        belong to the package of the entry which cites it: `core`, because
        every package error is a further condition on top of the core rules,
        or the package of the citing entry, which for an attribute is the
        package of the attribute when it states one, else the package of its
        type.

        Raises:
            GlossaryError: with every attribute which the report adds and
                which still states `required`, with every rule which is no
                validation rule of libsbml, and with every rule which belongs
                to a package foreign to the entry which cites it.
        """
        problems: list[str] = []
        for key, entry in self.entries():
            section, _, rest = key.partition(".")
            is_attribute = section == "types" and ".attributes." in rest
            if is_attribute and entry.spec is None and entry.required is not None:
                problems.append(
                    f"{_where(key, self.owners)}: the report adds the attribute, "
                    f"it cannot be required"
                )
            owner = self.types.get(rest.split(".", 1)[0]) if is_attribute else None
            for code in entry.rules:
                try:
                    package = resolve_rule(code).package
                except UnknownRuleError:
                    problems.append(
                        f"{_where(key, self.owners)}: the rule {code} is not a "
                        f"rule of libsbml"
                    )
                    continue
                allowed = {"core", entry.package}
                if owner is not None:
                    allowed.add(owner.package)
                if package not in allowed:
                    expected = (
                        entry.package
                        if entry.package != "core"
                        else (owner.package if owner is not None else entry.package)
                    )
                    problems.append(
                        f"{_where(key, self.owners)}: the rule {code} is a rule "
                        f"of {package}, the entry belongs to {expected}"
                    )
        if problems:
            raise GlossaryError("\n".join(["technical details:", *problems]))

    def validate_types(self) -> None:
        """Check that every `type` resolves and that every data type is used.

        Raises:
            GlossaryError: with every `type` of an entry which resolves to
                neither a data type nor a type of the glossary, with every
                `type` which resolves to both, and with every data type which
                no attribute names as its `type` and no data type relates to.
        """
        problems: list[str] = []
        used: set[str] = set()
        for key, entry in self.entries():
            if entry.type is None:
                continue
            stripped = entry.type.removesuffix("[]")
            in_datatypes = stripped in self.datatypes
            in_types = stripped in self.types
            if in_datatypes and in_types:
                problems.append(
                    f"{_where(key, self.owners)}: the type '{entry.type}' is "
                    f"both a data type and a type of the glossary"
                )
            elif not in_datatypes and not in_types:
                problems.append(
                    f"{_where(key, self.owners)}: the type '{entry.type}' is "
                    f"neither a data type nor a type of the glossary"
                )
            elif in_datatypes:
                used.add(stripped)
        for entry in self.datatypes.values():
            used.update(name for name in entry.related if name in self.datatypes)
        problems += [
            f"{_where(f'datatypes.{key}', self.owners)}: the data type is not used"
            for key in self.datatypes
            if key not in used
        ]
        if problems:
            raise GlossaryError("\n".join(["data types:", *problems]))

    def validate_required(self) -> None:
        """Check that every attribute of a specification states `required`.

        Raises:
            GlossaryError: with every attribute which cites a `spec` and does
                not state whether it is `required`.
        """
        problems = [
            f"{_where(key, self.owners)}: the attribute cites a specification "
            f"and does not state whether it is required"
            for key, entry in self.entries()
            if ".attributes." in key
            and entry.spec is not None
            and entry.required is None
        ]
        if problems:
            raise GlossaryError("\n".join(["required:", *problems]))

    def _validate_references(self) -> None:
        """Check that every `spec` and every `related` entry exists.

        A `related` type of a type entry names a type, a `related` type of a
        data type names a data type.
        """
        for key, entry in self.entries():
            if entry.spec is not None and entry.spec.doc not in self.specs:
                raise GlossaryError(
                    f"{_where(key, self.owners)}: the spec document "
                    f"'{entry.spec.doc}' is not defined, known documents are "
                    f"{', '.join(sorted(self.specs)) or 'none'}"
                )
            section = key.split(".", 1)[0]
            related_entries = self.datatypes if section == "datatypes" else self.types
            for name in entry.related:
                if name not in related_entries:
                    raise GlossaryError(
                        f"{_where(key, self.owners)}: the related type '{name}' has "
                        f"no entry"
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


def _optional_string(
    path: str, table: Mapping[str, Any], key: str, owners: Mapping[str, Path]
) -> str | None:
    """One optional string of an entry, absent or a string with a value."""
    value = table.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise GlossaryError(f"{_where(path, owners)}: '{key}' is not a string")
    return value.strip()


def _optional_bool(
    path: str, table: Mapping[str, Any], key: str, owners: Mapping[str, Path]
) -> bool | None:
    """One optional boolean of an entry, absent or `true`/`false`."""
    value = table.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise GlossaryError(f"{_where(path, owners)}: '{key}' is not a boolean")
    return value


def _string_list(
    path: str, table: Mapping[str, Any], key: str, owners: Mapping[str, Path]
) -> tuple[str, ...]:
    """One optional list of strings of an entry, `values` of a data type."""
    value = table.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise GlossaryError(f"{_where(path, owners)}: '{key}' is not a list of strings")
    return tuple(value)


def _rules(
    path: str, table: Mapping[str, Any], owners: Mapping[str, Path]
) -> tuple[int, ...]:
    """The `rules` of an entry: the numbers of the validation rules it cites.

    The numbers are read as written, not resolved against libsbml here;
    `Glossary.validate_technical` resolves them and reports a number which is
    no rule of libsbml or belongs to a foreign package.
    """
    value = table.get("rules", [])
    if not isinstance(value, list) or not all(
        isinstance(item, int) and not isinstance(item, bool) for item in value
    ):
        raise GlossaryError(
            f"{_where(path, owners)}: 'rules' is not a list of rule numbers"
        )
    seen: set[int] = set()
    for code in value:
        if code in seen:
            raise GlossaryError(
                f"{_where(path, owners)}: the rule {code} is listed twice"
            )
        seen.add(code)
    return tuple(value)


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
    short = table.get("short")
    return SpecDocument(
        key=key,
        label=_string(path, table, "label", owners),
        citation=_string(path, table, "citation", owners),
        url=_string(path, table, "url", owners),
        short=_string(path, table, "short", owners) if short is not None else key,
    )


def _spec_ref(value: Any, path: str, owners: Mapping[str, Path]) -> SpecRef:
    """The `spec` of an entry."""
    table = _table(path, value, owners)
    _known_keys(path, table, _SPEC_KEYS, owners)
    section = table.get("section")
    if section is not None and not isinstance(section, str):
        raise GlossaryError(f"{_where(path, owners)}: 'section' is not a string")
    return SpecRef(doc=_string(path, table, "doc", owners), section=section)


_ENTRY_KEYS_OF_KIND: Mapping[str, frozenset[str]] = {
    "type": _ENTRY_KEYS,
    "nested": _ATTRIBUTE_KEYS,
    "datatype": _DATATYPE_KEYS,
}


def _entry(
    key: str,
    value: Any,
    path: str,
    owners: Mapping[str, Path],
    *,
    kind: Literal["type", "nested", "datatype"],
) -> Entry:
    """One entry of the glossary, with its attributes when it is a type.

    Args:
        key: the key of the entry, the name of the type, of the field or of the
            data type.
        value: the table of the entry.
        path: the dotted path of the entry, for the error messages.
        owners: the file every key was read from.
        kind: `"type"` for a type, which may carry attributes and related
            types; `"nested"` for an attribute, a link kind or a concept,
            which may state whether it is required and which rules apply to
            it, but carries neither attributes nor related types; `"datatype"`
            for a data type, which may carry related data types and the closed
            set of `values` it takes, but neither attributes nor rules.
    """
    table = _table(path, value, owners)
    _known_keys(path, table, _ENTRY_KEYS_OF_KIND[kind], owners)
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
    required = (
        _optional_bool(path, table, "required", owners) if kind == "nested" else None
    )
    default = (
        _optional_string(path, table, "default", owners) if kind == "nested" else None
    )
    if default is not None and default.endswith("."):
        raise GlossaryError(
            f"{_where(path, owners)}: the default ends with a period, it is one clause"
        )
    if default is not None and required is not False:
        raise GlossaryError(
            f"{_where(path, owners)}: 'default' is given without 'required = false'"
        )
    return Entry(
        key=key,
        label=_string(path, table, "label", owners),
        summary=summary,
        description=_string(path, table, "description", owners),
        package=str(table.get("package", "core")),
        spec=None if spec is None else _spec_ref(spec, f"{path}.spec", owners),
        type=_optional_string(path, table, "type", owners),
        related=tuple(related),
        attributes={
            name: _entry(
                name, attribute, f"{path}.attributes.{name}", owners, kind="nested"
            )
            for name, attribute in _table(
                f"{path}.attributes", attributes, owners
            ).items()
        },
        required=required,
        default=default,
        rules=_rules(path, table, owners) if kind in ("type", "nested") else (),
        values=_string_list(path, table, "values", owners)
        if kind == "datatype"
        else (),
    )


def _read(path: Path) -> str:
    """The content of a file the check reads, as a message instead of an OSError."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise GlossaryError(f"{path} cannot be read: {error}") from error


def _edge_kinds(path: Path) -> list[str]:
    """The `EDGE_KINDS` array of the frontend."""
    match = _EDGE_KINDS.search(_read(path))
    if match is None:
        raise GlossaryError(f"{path}: no EDGE_KINDS array")
    return re.findall(r'"([^"]+)"', match.group("kinds"))


def _ref(schema: Any) -> str | None:
    """The definition a property references directly, not through a list."""
    if not isinstance(schema, Mapping):
        return None
    target = schema.get("$ref")
    if isinstance(target, str):
        return target.rsplit("/", 1)[-1]
    for option in schema.get("anyOf", []):
        name = _ref(option)
        if name is not None:
            return name
    return None


def _fields(
    defs: Mapping[str, Any], properties: Mapping[str, Any], name: str
) -> list[str]:
    """The names the property of a report type needs an entry for.

    A property which holds a value, a list or an element of its own is one
    entry. A property which holds an object the report shows field by field,
    the comp or the fbc extension of an element or the trigger of an event, is
    explained field by field as `<property>.<field>`.
    """
    referenced = _ref(properties.get(name))
    if referenced is None or referenced in SINGLE_VALUE_DEFINITIONS:
        return [name]
    nested = defs.get(referenced, {}).get("properties", {})
    if not nested or set(nested) >= SBASE_PROPERTIES:
        # an element of the report, which has a type entry and a page of its own
        return [name]
    return [f"{name}.{field}" for field in nested]


def _known_fields(defs: Mapping[str, Any], properties: Mapping[str, Any]) -> set[str]:
    """Every name an attribute entry of a type may carry.

    The property itself, which an entry may explain as a whole, the names
    `_fields` asks an entry for, and `<property>.<field>` of an element the
    property holds, which the report shows as a column of its own.
    """
    names: set[str] = set()
    for name, schema in properties.items():
        names.add(name)
        names.update(_fields(defs, properties, name))
        referenced = _ref(schema)
        nested = defs.get(referenced, {}).get("properties", {}) if referenced else {}
        names.update(f"{name}.{field_name}" for field_name in nested)
    return names


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


def _link_problem(
    target: str,
    anchors: Mapping[str, set[str]],
    home: str,
    root: Path | None,
) -> str | None:
    """What is wrong with the target of a link of a description, or nothing.

    Args:
        target: the target of the link, as the description writes it.
        anchors: the anchors of every generated reference page, by file name.
        home: the page the description is rendered on, the page a bare `#anchor`
            points into.
        root: the repository root, when a page outside the reference can be read.
    """
    page, _, fragment = target.partition("#")
    if page and _EXTERNAL.match(page):
        return None
    if page.startswith("../"):
        # a page of the site outside the reference, for example `../sbml.md`;
        # it exists when the documentation is built
        if root is None:
            return None
        path = root / DOCS_DIR / page[3:]
        if not path.is_file():
            return "does not resolve to a page of the documentation"
        if fragment and fragment not in set(_anchors_of(_read(path))):
            return "does not resolve to an anchor of that page"
        return None
    page = page or home
    if page not in anchors:
        return "does not resolve to a reference page"
    if fragment and fragment not in anchors[page]:
        return f"does not resolve to an anchor of {page}"
    return None


def _navigation_pages(nav: Any) -> Iterator[str]:
    """Every page the navigation of the site names, however deeply it is nested."""
    if isinstance(nav, str):
        yield nav
    elif isinstance(nav, list):
        for item in nav:
            yield from _navigation_pages(item)
    elif isinstance(nav, Mapping):
        for value in nav.values():
            yield from _navigation_pages(value)


def _sentence(summary: str) -> str:
    """A summary as a sentence, for the lead paragraph of a page."""
    return f"{summary[:1].upper()}{summary[1:]}."


def _cell(text: str | None) -> str:
    """One cell of a markdown table, a dash when there is nothing to show."""
    return (text or "-").replace("|", "\\|")


def _spec_label(document: SpecDocument, spec: SpecRef) -> str:
    """The label of a section of a specification, for example `core 4.6.3`.

    It names the document and the section, so that a table of a type which
    mixes the core specification with a package says which document a section
    belongs to.
    """
    return f"{document.short} {spec.section}" if spec.section else document.short


def _spec_link(glossary: Glossary, spec: SpecRef | None) -> str:
    """The specification section of an entry as a link into the document."""
    if spec is None:
        return "-"
    document = glossary.specs[spec.doc]
    return f"[{_spec_label(document, spec)}]({document.url})"


def _required_cell(required: bool | None) -> str:
    """The `required` column of an attribute row: `required`, `optional` or `-`."""
    if required is None:
        return "-"
    return "required" if required else "optional"


def _escape_rule_message(message: str) -> str:
    """A rule message with its angle brackets escaped so markdown shows them literally.

    A message of libsbml names an element with an angle bracket, `<species>`,
    which markdown would otherwise read as an (unknown) html tag.
    """
    return message.replace("<", "&lt;").replace(">", "&gt;")


def _rule_lines(rules: Iterable[Rule]) -> list[str]:
    """One list item per validation rule: its number, its severity and its message."""
    return [
        f"- `{rule.id}` ({rule.severity}): {_escape_rule_message(rule.message)}"
        for rule in rules
    ]


def _type_cell(
    glossary: Glossary, type_name: str | None, datatype_anchors: Mapping[str, str]
) -> str:
    """The `type` column of an attribute row, linking its data type or its type page.

    Args:
        glossary: the glossary to resolve the type against.
        type_name: the `type` of the attribute, as written.
        datatype_anchors: the anchor of every data type on `datatypes.md`, from
            `_datatype_anchors`.
    """
    if not type_name:
        return "-"
    key = glossary.type_key(type_name)
    if key is None:
        return f"`{type_name}`"
    section, _, name = key.partition("/")
    href = (
        f"{DATATYPES_PAGE}#{datatype_anchors[name]}"
        if section == "datatypes"
        else f"{glossary.types[name].slug}.md"
    )
    return f"[`{type_name}`]({href})"


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
    glossary: Glossary,
    attributes: Iterable[Entry],
    anchors: Mapping[str, str],
    datatype_anchors: Mapping[str, str],
    *,
    with_spec: bool,
) -> list[list[str]]:
    """One row per attribute, its label linking the block which describes it.

    `with_spec` also decides whether the row states `required`: a field the
    report adds cites no specification and is therefore never required, so
    the table of the report fields carries no such column.
    """
    rows = []
    for attribute in attributes:
        row = [
            f"[{_cell(attribute.label)}](#{anchors[attribute.key]})",
            _type_cell(glossary, attribute.type, datatype_anchors),
        ]
        if with_spec:
            row.append(_required_cell(attribute.required))
        row.append(_cell(attribute.summary))
        if with_spec:
            row.append(_spec_link(glossary, attribute.spec))
        rows.append(row)
    return rows


def _attribute_details(
    glossary: Glossary, attributes: Iterable[Entry], anchors: Mapping[str, str]
) -> list[str]:
    """One block per attribute: its anchor and its label, then its description.

    The table above is the index, the blocks are what a reader of a single
    attribute wants, and the anchor of the block is what the row of the table
    and every link of the site point at. A default is stated as a paragraph of
    its own below the description, and the rules the attribute cites follow as
    a list.
    """
    lines: list[str] = []
    for attribute in attributes:
        lines += [
            f'<span id="{anchors[attribute.key]}"></span>**{attribute.label}**',
            "",
            attribute.description,
            "",
        ]
        if attribute.default is not None:
            lines += [f"Default: {attribute.default}.", ""]
        rules = glossary.resolved_rules(attribute)
        if rules:
            lines += [*_rule_lines(rules), ""]
    return lines


def _type_page_anchors(entry: Entry) -> dict[str, str]:
    """The anchor of every attribute and report field of a type page, by attribute key.

    The headings of the page are reserved first, so that an attribute never
    collides with `## Attributes`, `## In the report`, `## Related elements` or
    `## Specification`, and two attributes of one type which share a label
    still get an anchor of their own each.

    Args:
        entry: the type entry.
    """
    attributes = [a for a in entry.attributes.values() if a.package != "report"]
    report_fields = [a for a in entry.attributes.values() if a.package == "report"]
    return _entry_anchors(
        [*attributes, *report_fields],
        [anchor(entry.label), *(anchor(heading) for heading in PAGE_HEADINGS)],
    )


def _datatype_anchors(glossary: Glossary) -> dict[str, str]:
    """The anchor of every data type on `datatypes.md`, by its key.

    `render_datatypes_page`, `_link_keys` and the `docs` field of the details
    share this one computation, so that a `docs` url and a `glossary:datatypes/...`
    link can never point at an anchor the rendered page does not have.

    Args:
        glossary: the glossary to build the map from.
    """
    return _entry_anchors(glossary.datatypes.values(), ())


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
    report_fields = [a for a in entry.attributes.values() if a.package == "report"]
    anchors = _type_page_anchors(entry)
    datatype_anchors = _datatype_anchors(glossary)

    rows = _attribute_rows(
        glossary, attributes, anchors, datatype_anchors, with_spec=True
    )
    if rows:
        lines += ["## Attributes", ""]
        lines += _table_rows(
            ["attribute", "type", "required", "meaning", "specification"], rows
        )
        lines += [""]
    if entry.key not in NON_ELEMENT_TYPES and "SBase" in glossary.types:
        lines += [
            "Every element of a model also carries the "
            "[common attributes](sbase.md) of `SBase`.",
            "",
        ]
    lines += _attribute_details(glossary, attributes, anchors)

    rows = _attribute_rows(
        glossary, report_fields, anchors, datatype_anchors, with_spec=False
    )
    if rows:
        lines += ["## In the report", ""]
        lines += _table_rows(["field", "type", "meaning"], rows)
        lines += [""]
        lines += _attribute_details(glossary, report_fields, anchors)

    if entry.rules:
        lines += [
            "## Validation rules",
            "",
            *_rule_lines(glossary.resolved_rules(entry)),
            "",
        ]

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
        f"the report computes on top of the model, and the [data types]"
        f"({DATATYPES_PAGE}) explain the values its attributes and its fields carry.",
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


def render_datatypes_page(glossary: Glossary) -> str:
    """The page of the data types an attribute or a field of the report may carry.

    Rendered even when the glossary has no data type yet, so that the page,
    its entry of the navigation and every link into it stay stable from the
    moment this module ships.

    Args:
        glossary: the glossary to render.

    Returns:
        The markdown of `docs/reference/datatypes.md`, one `##` section per
        data type.
    """
    anchors = _datatype_anchors(glossary)
    lines = [
        "# Data types",
        "",
        "A data type is the kind of value an attribute or a field the report adds "
        "carries, for example a number, an identifier or a fragment of markup. The "
        "`type` column of every other page of the reference links here.",
        "",
    ]
    for entry in glossary.datatypes.values():
        lines += [
            f"## `{entry.label}` {{#{anchors[entry.key]}}}",
            "",
            _sentence(entry.summary),
            "",
            entry.description,
        ]
        if entry.values:
            lines += ["", *[f"- `{value}`" for value in entry.values]]
        if entry.spec is not None:
            document = glossary.specs[entry.spec.doc]
            section = f", Section {entry.spec.section}" if entry.spec.section else ""
            lines += ["", f"[{document.label}]({document.url}){section}."]
        lines += [""]
    return "\n".join(lines).rstrip("\n") + "\n"


def render_json(glossary: Glossary) -> dict[str, Any]:
    """The entries the application reads, without the descriptions.

    Args:
        glossary: the glossary to render.

    Returns:
        The content of `frontend/src/data/glossary.json`, sorted by key. The
        `page` of a type is the path of its reference page below the url of the
        documentation site, which the inspector links; a link kind and a concept
        carry the label and the summary of their tooltip and nothing else.
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
        "links": _render_json_entries(glossary.links),
        "concepts": _render_json_entries(glossary.concepts),
    }


def _render_json_entries(entries: Mapping[str, Entry]) -> dict[str, Any]:
    """The link kinds or the concepts of the json, the tooltips of the application."""
    return {
        key: {"label": entry.label, "summary": entry.summary}
        for key, entry in sorted(entries.items())
    }


def entry_key(dotted: str) -> str:
    """The key of an entry in `frontend/src/data/glossary-details.json`.

    Args:
        dotted: the key of the entry as `Glossary.entries()` yields it, for
            example `types.Species.attributes.initialAmount`.

    Returns:
        `types/Species/initialAmount`, `links/compartment`,
        `concepts/derivedUnits` or `datatypes/double`. An attribute key may
        carry a dot of its own (`fbc.charge`), so the split happens on the
        literal `.attributes.` and on the first dot only, never on every dot.
    """
    section, _, rest = dotted.partition(".")
    type_name, separator, attribute_name = rest.partition(".attributes.")
    if separator:
        return f"{section}/{type_name}/{attribute_name}"
    return f"{section}/{rest}"


_KIND_OF_SECTION: Mapping[str, str] = {
    "links": "link",
    "concepts": "concept",
    "datatypes": "datatype",
}


def _link_keys(glossary: Glossary) -> dict[str, dict[str, str]]:
    """The key every anchor of every reference page resolves to, by page name.

    The empty string is the anchor of the page itself. `links.md`,
    `concepts.md` and `datatypes.md` carry no such empty key, because none of
    the three explains anything of its own: `rewrite_links` turns a bare link
    to one of them into the absolute url of the site instead of a `glossary:`
    key, exactly as it does for `index.md`, which is not a page of this map at
    all.

    Args:
        glossary: the glossary to build the map from.
    """
    keys: dict[str, dict[str, str]] = {}
    for entry in glossary.types.values():
        page = f"{entry.slug}.md"
        type_key = f"types/{entry.key}"
        anchors: dict[str, str] = {"": type_key}
        for heading in (anchor(entry.label), *(anchor(h) for h in PAGE_HEADINGS)):
            anchors[heading] = type_key
        for name, attribute_anchor in _type_page_anchors(entry).items():
            anchors[attribute_anchor] = f"types/{entry.key}/{name}"
        keys[page] = anchors
    keys[LINKS_PAGE] = {
        anchor(entry.label): f"links/{entry.key}" for entry in glossary.links.values()
    }
    keys[CONCEPTS_PAGE] = {
        anchor(entry.label): f"concepts/{entry.key}"
        for entry in glossary.concepts.values()
    }
    datatype_anchors = _datatype_anchors(glossary)
    keys[DATATYPES_PAGE] = {
        datatype_anchors[entry.key]: f"datatypes/{entry.key}"
        for entry in glossary.datatypes.values()
    }
    return keys


def _site_url(page: str, fragment: str) -> str:
    """The absolute url of a page of the site, in its directory url form.

    Args:
        page: the page relative to the root of the documentation, with its
            `.md` suffix; `index.md` is the root of the site, and `index.md`
            of a directory (`reference/index.md`) is that directory itself,
            never a trailing `.../index/` segment of its own.
        fragment: the anchor of the page, or an empty string for the page
            itself.
    """
    slug = page.removesuffix(".md")
    if slug == "index" or slug.endswith("/index"):
        slug = slug.removesuffix("index").rstrip("/")
    base = DOCS_URL if not slug else f"{DOCS_URL}{slug}/"
    return f"{base}#{fragment}" if fragment else base


def rewrite_links(
    description: str, home: str, keys: Mapping[str, Mapping[str, str]]
) -> str:
    """Rewrite every link of a description for the help dialog.

    A link into the generated reference becomes a `glossary:<key>` link, which
    the frontend resolves by opening the entry of that key instead of
    following it; a link to a page of the site outside the reference, written
    `../page.md`, and a link to a page of the reference which explains nothing
    of its own become the absolute url of that page on the documentation site.
    An external link and an image are left untouched.

    Args:
        description: the markdown of one entry.
        home: the page the entry is rendered on, the page a bare `#anchor`
            link points into.
        keys: the key of every anchor of every reference page, from
            `_link_keys`.

    Returns:
        The description with every link target rewritten.

    Raises:
        GlossaryError: a link does not resolve through `keys` or through a
            page of the site outside the reference.
    """

    def replace(match: re.Match[str]) -> str:
        text, target = match.group(1), match.group(2)
        page, _, fragment = target.partition("#")
        if page and _EXTERNAL.match(page):
            return match.group(0)
        if page.startswith("../"):
            return f"[{text}]({_site_url(page[3:], fragment)})"
        page = page or home
        if page != INDEX_PAGE:
            key = keys.get(page, {}).get(fragment)
            if key is not None:
                return f"[{text}](glossary:{key})"
            if fragment:
                raise GlossaryError(f"the link [{text}]({target}) does not resolve")
        return f"[{text}]({_site_url(f'{REFERENCE_DIR.name}/{page}', fragment)})"

    return _LINK.sub(replace, description)


def _spec_detail(glossary: Glossary, spec: SpecRef) -> dict[str, str]:
    """The `spec` field of a details entry."""
    document = glossary.specs[spec.doc]
    detail: dict[str, str] = {"label": _spec_label(document, spec), "url": document.url}
    if spec.section:
        detail["section"] = spec.section
    return detail


def _rule_detail(rule: Rule) -> dict[str, Any]:
    """One rule of the `rules` field of a details entry."""
    detail: dict[str, Any] = {
        "id": rule.id,
        "severity": rule.severity,
        "message": rule.message,
    }
    if rule.section:
        detail["section"] = rule.section
    return detail


def _render_detail(
    dotted: str,
    entry: Entry,
    glossary: Glossary,
    keys: Mapping[str, Mapping[str, str]],
    datatype_anchors: Mapping[str, str],
) -> dict[str, Any]:
    """One entry of `frontend/src/data/glossary-details.json`.

    Args:
        dotted: the key of the entry as `Glossary.entries()` yields it.
        entry: the entry itself.
        glossary: the glossary the entry belongs to, to resolve its `spec`,
            its `type` and the links of its description.
        keys: the key of every anchor of every reference page, from
            `_link_keys`.
        datatype_anchors: the anchor of every data type on `datatypes.md`,
            from `_datatype_anchors`, so that `docs` of a data type is the
            anchor `render_datatypes_page` gives it.

    Returns:
        The entry of the `entries` map of the details, a field left out when
        the entry does not state it.

    Raises:
        GlossaryError: a link of the description does not resolve, or a `type`
            of the entry resolves to neither a data type nor a type of the
            glossary.
    """
    section, _, rest = dotted.partition(".")
    type_name, separator, attribute_name = rest.partition(".attributes.")
    is_attribute = bool(separator)
    home = glossary.page_of(dotted)
    try:
        description = rewrite_links(entry.description, home, keys)
    except GlossaryError as error:
        raise GlossaryError(f"{entry_key(dotted)}: {error}") from error

    if is_attribute:
        owner = glossary.types[type_name]
        kind = "attribute"
        docs = (
            f"{REFERENCE_DIR.name}/{owner.slug}/"
            f"#{_type_page_anchors(owner)[attribute_name]}"
        )
    elif section == "types":
        kind = "type"
        docs = f"{REFERENCE_DIR.name}/{entry.slug}/"
    elif section == "datatypes":
        kind = _KIND_OF_SECTION[section]
        docs = f"{REFERENCE_DIR.name}/{section}/#{datatype_anchors[entry.key]}"
    else:
        kind = _KIND_OF_SECTION[section]
        docs = f"{REFERENCE_DIR.name}/{section}/#{anchor(entry.label)}"

    detail: dict[str, Any] = {
        "kind": kind,
        "label": entry.label,
        "summary": entry.summary,
        "description": description,
        "package": entry.package,
        "docs": docs,
    }
    if is_attribute:
        detail["owner"] = f"types/{type_name}"
    if entry.type is not None:
        type_key = glossary.type_key(entry.type)
        if type_key is None:
            raise GlossaryError(
                f"{_where(dotted, glossary.owners)}: the type '{entry.type}' "
                f"resolves to nothing"
            )
        detail["type"] = {"label": entry.type, "key": type_key}
    if entry.spec is not None:
        detail["spec"] = _spec_detail(glossary, entry.spec)
    if entry.required is not None:
        detail["required"] = entry.required
    if entry.default is not None:
        detail["default"] = entry.default
    rules = glossary.resolved_rules(entry)
    if rules:
        detail["rules"] = [_rule_detail(rule) for rule in rules]
    if kind == "type":
        if entry.attributes:
            detail["attributes"] = [
                entry_key(f"types.{entry.key}.attributes.{name}")
                for name in entry.attributes
            ]
        if entry.related:
            detail["related"] = [f"types/{name}" for name in entry.related]
    if kind == "datatype":
        if entry.related:
            detail["related"] = [f"datatypes/{name}" for name in entry.related]
        if entry.values:
            detail["values"] = list(entry.values)
    return detail


def render_details(glossary: Glossary) -> dict[str, Any]:
    """The description and the technical details of every entry, for the help dialog.

    Args:
        glossary: the glossary to render.

    Returns:
        The content of `frontend/src/data/glossary-details.json`: one entry
        per key of `Glossary.entries()`, sorted by key, a field left out when
        the entry does not state it.

    Raises:
        GlossaryError: a link of a description does not resolve to a
            `glossary:` key or to a page of the site outside the reference, or
            a `type` of an entry resolves to neither a data type nor a type of
            the glossary.
    """
    keys = _link_keys(glossary)
    datatype_anchors = _datatype_anchors(glossary)
    entries = {
        entry_key(dotted): _render_detail(
            dotted, entry, glossary, keys, datatype_anchors
        )
        for dotted, entry in glossary.entries()
    }
    return {"entries": dict(sorted(entries.items()))}


def _reference_pages(glossary: Glossary) -> dict[str, str]:
    """Every generated reference page with its markdown, by file name."""
    pages = {
        INDEX_PAGE: render_index_page(glossary),
        LINKS_PAGE: render_links_page(glossary),
        CONCEPTS_PAGE: render_concepts_page(glossary),
        DATATYPES_PAGE: render_datatypes_page(glossary),
    }
    for entry in glossary.types.values():
        pages[f"{entry.slug}.md"] = render_type_page(glossary, entry)
    return pages


def _files(glossary: Glossary) -> dict[Path, str]:
    """Every generated file with its content, relative to the repository root."""
    files: dict[Path, str] = {
        JSON_PATH: json.dumps(render_json(glossary), indent=2, ensure_ascii=False)
        + "\n",
        DETAILS_PATH: json.dumps(render_details(glossary), indent=2, ensure_ascii=False)
        + "\n",
    }
    for name, page in _reference_pages(glossary).items():
        files[REFERENCE_DIR / name] = page
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
            lambda: glossary.validate_labels(),
            lambda: glossary.validate_technical(),
            lambda: glossary.validate_types(),
            lambda: glossary.validate_required(),
            lambda: glossary.validate_links(root),
            lambda: glossary.validate_navigation(root),
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
