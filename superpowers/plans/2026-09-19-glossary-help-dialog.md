# Help dialog of the report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** every type, attribute, link kind, concept and data type of the report opens in a navigable help dialog which explains it on the high level (the descriptions of the glossary) and on the low level (data type, required, default, validation rules, specification).

**Architecture:** `glossary/*.toml` stays the single source. It gains `required`, `default` and `rules` (libsbml rule numbers, resolved by the generator) on its entries and a section `datatypes`. `sbml4humans.glossary` writes a third output, `frontend/src/data/glossary-details.json`, with the descriptions as markdown whose reference links are rewritten to `glossary:<key>`, and extends the reference pages. The frontend loads the details and `markdown-it` lazily with the first dialog; the open entry is the route query `help=<key>`.

**Tech Stack:** python 3.14, python-libsbml, pytest, ruff, ty; Vue 3.5, TypeScript, Vue Router 5, Tailwind 4, `@lucide/vue`, DOMPurify, new: `markdown-it` (MIT) with `@types/markdown-it`; vitest, Playwright.

**Spec:** `superpowers/specs/2026-09-19-glossary-help-dialog-design.md`

## Global Constraints

- Never the em dash, a plain dash instead. Markdown and TOML descriptions carry no hard line wraps.
- No co-author line in a commit message. Never edit `CHANGELOG.md` or a generated file by hand (`glossary.json`, `glossary-details.json`, `docs/reference/*.md`, `docs/release-notes.md`, `src/types/report.ts`).
- Backend: every module, class and function annotated and with a google style docstring; `uv run ruff check . && uv run ruff format --check . && uv run ty check` at zero diagnostics; libsbml objects annotated explicitly, getters instead of SWIG attributes; suppressions only as `# ty: ignore[rule]`.
- The glossary is the only place where something is named or explained; the frontend states no label or explanation of its own.
- Frontend: node 22 is what this machine has (no nvm), `npm run lint && npm run typecheck && npm run test:unit` green; every element an end to end test touches carries a `data-testid`; components resolve cross references through `ReportIndex`; new dependencies MIT, ISC or comparable, committed with `package-lock.json`.
- `glossary.json` stays byte-identical: the initial bundle must not grow by the details.
- A rule text is never written by hand, only its number is cited.
- Commands: backend from `backend/` (`uv run ...`), frontend from `frontend/`, the glossary generator `uv run python -m sbml4humans.glossary [--check]` from `backend/`, the site `uv run --project backend zensical build --clean --strict` from the root. End to end tests need the backend on port 1444 (`uv run uvicorn sbml4humans.api:api --port 1444`).

## File Structure

| file | responsibility |
| --- | --- |
| `backend/sbml4humans/glossaryrules.py` (new) | resolve a libsbml rule number into `Rule`; the only glossary module which imports libsbml |
| `backend/sbml4humans/glossary.py` | read the new keys and `datatypes`, validate them, render the details json, the extended pages and `datatypes.md` |
| `backend/tests/test_glossaryrules.py` (new), `backend/tests/test_glossary.py`, `backend/tests/data/glossary/*.toml` | tests and the fixture glossary |
| `glossary/core.toml`, `glossary/packages.toml`, `glossary/report.toml` | the content |
| `frontend/src/report/glossary.ts` | the keys of the entries, one lookup shared by label, tooltip and key |
| `frontend/src/report/glossaryDetails.ts` (new) | the types of the details and the cached lazy load |
| `frontend/src/report/helpMarkdown.ts` (new) | markdown to sanitised html, the only importer of `markdown-it` |
| `frontend/src/report/query.ts`, `view.ts` | `help` in the view state, `openHelp`, `closeHelp`, `helpRoute` |
| `frontend/src/components/help/HelpDialog.vue`, `HelpMarkdown.vue`, `HelpLabel.vue`, `HelpButton.vue` (new) | the dialog and its two openers |
| `AttributeRow.vue`, `InspectorPanel.vue`, `LinksColumn.vue`, `NestedTable.vue`, `ElementTable.vue`, `ElementSection.vue`, `ReportPage.vue` | the entry points and the mount |
| `frontend/tests/unit/help*.test.ts`, `glossary.test.ts`, `query.test.ts`, `frontend/tests/e2e/help.spec.ts` | tests |
| `docs/report.md`, `docs/development.md`, `zensical.toml`, `CLAUDE.md`, `release-notes/0.7.0.md`, `frontend/scripts/screenshots.mjs` | documentation |

---

### Task 1: Resolve a validation rule with libsbml

**Files:**
- Create: `backend/sbml4humans/glossaryrules.py`
- Test: `backend/tests/test_glossaryrules.py`

**Interfaces:**
- Produces: `Rule(id: int, package: str, severity: str, message: str, section: str | None)` (frozen dataclass, `severity` is `"error"` or `"warning"`), `UnknownRuleError(ValueError)`, `rule_package(code: int) -> str`, `resolve_rule(code: int) -> Rule`.

Verified facts about libsbml (do not re-derive): `SBMLError(20609, 3, 2)` answers message, severity and category of a core rule; an unknown core number has an empty message (99999) or the category "Internal" (12345). The `SBMLError` constructor echoes the severity of its caller for a package rule, so a package rule is read from its extension: `ext = SBMLExtensionRegistry.getInstance().getExtension("comp")`, `ext.getErrorIdOffset()` (comp 1000000, distrib 1500000, fbc 2000000, qual 3000000), `index = ext.getErrorTableIndex(code)` (0 = unknown), `ext.getSeverity(index, pkg_version)`, `ext.getMessage(index, pkg_version, "")`. `LIBSBML_SEV_NOT_APPLICABLE` means the rule does not exist in that version: fbc 2020201-like rules of V1 only, core rules of L2 or L3V1. A message ends with `Reference: L3V2 Section 4.6.4` for most rules, not for all.

- [ ] **Step 1: Write the failing tests**

```python
"""Tests of the resolution of the validation rules of libsbml."""

import pytest

from sbml4humans.glossaryrules import Rule, UnknownRuleError, resolve_rule, rule_package


def test_resolves_a_core_rule() -> None:
    rule = resolve_rule(20609)
    assert rule == Rule(
        id=20609,
        package="core",
        severity="error",
        message=(
            "A <species> cannot set values for both 'initialConcentration' and "
            "'initialAmount' because they are mutually exclusive."
        ),
        section="L3V2 Section 4.6.4",
    )


def test_resolves_a_warning() -> None:
    assert resolve_rule(20608).severity == "warning"


def test_resolves_a_package_rule_from_the_table_of_its_extension() -> None:
    rule = resolve_rule(1020101)
    assert rule.package == "comp"
    assert rule.severity == "error"
    assert rule.message.startswith("Any object derived from the extended SBase class")
    assert rule.section == "L3V1 Comp V1 Section 3.6"


def test_the_severity_of_a_package_rule_is_the_one_of_the_rule() -> None:
    # libsbml echoes the severity of the caller for a package rule, the table knows better
    assert resolve_rule(1090110).severity == "warning"


def test_a_rule_without_a_reference_has_no_section() -> None:
    assert resolve_rule(1090101).section is None


def test_a_rule_of_an_older_version_is_resolved_there() -> None:
    # the flux bounds exist in fbc version 1 only, which the report reads as well
    rules = [resolve_rule(code) for code in range(2020401, 2020410)]
    assert all(rule.message for rule in rules)


@pytest.mark.parametrize(
    ("code", "package"),
    [(20609, "core"), (1020101, "comp"), (1520101, "distrib"), (2020301, "fbc"), (3020101, "qual")],
)
def test_the_package_follows_from_the_number(code: int, package: str) -> None:
    assert rule_package(code) == package


@pytest.mark.parametrize("code", [99999, 12345, 1029999, 2099999, 0, -1])
def test_an_unknown_number_is_an_error(code: int) -> None:
    with pytest.raises(UnknownRuleError, match=str(code)):
        resolve_rule(code)
```

Before relying on `range(2020401, 2020410)`, list the fbc rules which are not applicable in V3 with a three line script and put real numbers of V1-only rules into the test; keep the intent (a rule which exists in an older version only resolves).

- [ ] **Step 2: Run them, they fail on the import**

Run: `uv run pytest tests/test_glossaryrules.py -q` - Expected: `ModuleNotFoundError: sbml4humans.glossaryrules`.

- [ ] **Step 3: Implement**

```python
"""The validation rules of SBML, resolved from their number with libsbml.

The glossary cites a rule by the number libsbml gives it and never writes its
text: the message, the severity and the section of the specification are read
from the tables of the library which also validates the model of a user.
"""

import re
from dataclasses import dataclass

import libsbml


PACKAGES = ("comp", "distrib", "fbc", "qual")

# the versions of core a rule is looked up in, the newest first: a rule which
# is not applicable there belongs to an older one, which the report reads too
_CORE_VERSIONS = ((3, 2), (3, 1), (2, 5))
_REFERENCE = re.compile(r"\s*Reference:\s*(?P<section>.+?)\s*$")
_SEVERITIES = {
    libsbml.LIBSBML_SEV_ERROR: "error",
    libsbml.LIBSBML_SEV_FATAL: "error",
    libsbml.LIBSBML_SEV_SCHEMA_ERROR: "error",
    libsbml.LIBSBML_SEV_WARNING: "warning",
    libsbml.LIBSBML_SEV_GENERAL_WARNING: "warning",
}


class UnknownRuleError(ValueError):
    """A number which is no validation rule of libsbml."""


@dataclass(frozen=True, slots=True)
class Rule:
    """One validation rule of a specification, as libsbml states it."""

    id: int
    package: str
    severity: str
    message: str
    section: str | None
```

`rule_package(code)`: `"core"` below the smallest offset, else the package with the largest `getErrorIdOffset()` not above the code; a code below 10000 raises `UnknownRuleError`. `resolve_rule(code)`: for core, the first of `_CORE_VERSIONS` whose `SBMLError(code, level, version)` has a severity in `_SEVERITIES`; unknown when the message is empty or `getCategoryAsString() == "Internal"` or no version applies. For a package, `index = ext.getErrorTableIndex(code)`, unknown when 0, then the versions of the package from the newest down (`ext.getNumOfSupportedPackageURI()`, `ext.getPackageVersion(ext.getSupportedPackageURI(i))`, deduplicated, sorted descending), the first with a severity in `_SEVERITIES`. `_message(text) -> tuple[str, str | None]` joins the whitespace (`" ".join(text.split())`) and splits the trailing reference off with `_REFERENCE`. Annotate every libsbml object (`error: libsbml.SBMLError`, `extension: libsbml.SBMLExtension`).

- [ ] **Step 4: Run the tests, ruff and ty**

Run: `uv run pytest tests/test_glossaryrules.py -q && uv run ruff check . && uv run ruff format --check . && uv run ty check` - Expected: all green.

- [ ] **Step 5: Commit**

`git add backend/sbml4humans/glossaryrules.py backend/tests/test_glossaryrules.py && git commit -m "Resolve a validation rule of SBML from its libsbml number"`

---

### Task 2: Read `required`, `default`, `rules`, `values` and the section `datatypes`

**Files:**
- Modify: `backend/sbml4humans/glossary.py` (`_ENTRY_KEYS`, `_ATTRIBUTE_KEYS`, `_SECTIONS`, `Entry`, `Glossary`, `_entry`, `entries`, `_validate_references`, new `validate_technical`, `validate_required`)
- Modify: `backend/tests/data/glossary/*.toml` (the fixture gains the new keys and a `datatypes` section)
- Test: `backend/tests/test_glossary.py`

**Interfaces:**
- Consumes: `resolve_rule`, `Rule`, `UnknownRuleError`, `rule_package` of Task 1.
- Produces: `Entry.required: bool | None`, `Entry.default: str | None`, `Entry.rules: tuple[int, ...]`, `Entry.values: tuple[str, ...]`; `Glossary.datatypes: Mapping[str, Entry]`; `Glossary.type_key(name: str) -> str | None` (`"datatypes/SId"`, `"types/KineticLaw"`, `None`); `Glossary.resolved_rules(entry: Entry) -> list[Rule]`; `Glossary.validate_technical() -> None`; `Glossary.validate_types() -> None`; `Glossary.validate_required() -> None`. `Glossary.entries()` also yields `datatypes.<key>`.

Key sets: `required`, `default`, `rules` join `_ATTRIBUTE_KEYS`; `rules` joins `_ENTRY_KEYS`; a new `_DATATYPE_KEYS = {"label", "summary", "description", "package", "spec", "related", "values"}`; `_SECTIONS` gains `"datatypes"`. `_entry` gets a keyword `kind: Literal["type", "nested", "datatype"]` instead of `nested: bool` (update its four callers). Parsing errors name the file and the path with `_where`, like the existing ones: `'required' is not a boolean`, `'rules' is not a list of rule numbers`, `the rule 20609 is listed twice`, `'default' is given for a required attribute`, `'values' is not a list of strings`. `related` of a datatype names datatypes.

Three validations, each collecting every problem before it raises a `GlossaryError`:

- `validate_technical` ("technical details:"), part of the checks of `main` from this task on, green on the repository glossary because it only judges what an entry states:
  - an attribute without a `spec` states `required`: `the report adds the attribute, it cannot be required`;
  - every rule resolves, else `the rule 99999 is not a rule of libsbml`; its `rule_package` is `core` or the package of the citing entry (of the attribute, else of its type), else `the rule 1020101 is a rule of comp, the entry belongs to fbc`.
- `validate_types` ("data types:"), a method now, a check of `main` in Task 9 when the content exists:
  - the `type` of an attribute resolves with `type_key`, else `the type 'Foo' is neither a data type nor a type of the glossary`; a name which is both a data type and a type is an error;
  - a data type which no attribute names as its `type` and no data type relates to: `the data type is not used`.
- `validate_required` ("required:"), a method now, a check of `main` in Task 9: every attribute with a `spec` states `required`.

- [ ] **Step 1: Extend the fixture glossary.** In `backend/tests/data/glossary/`, give `Species.initialAmount` `required = false`, `default = "set by an initial assignment or a rule"`, `rules = [20609]`, give the type `Species` `rules = [20601]`, give every other spec attribute `required`, and add `[datatypes.double]`, `[datatypes.SIdRef]` and whatever other `type` the fixture names (read the fixture first), one of them with `values`.
- [ ] **Step 2: Write the failing tests** in `test_glossary.py`, one per bullet above, in the style of `test_an_unknown_key_of_an_entry_is_an_error` (copy the fixture with `_repository(tmp_path, extra_glossary=...)`, assert on `GlossaryError` with `match=`). Names: `test_reads_the_technical_details`, `test_required_is_a_boolean`, `test_a_default_of_a_required_attribute_is_an_error`, `test_a_rule_listed_twice_is_an_error`, `test_an_unknown_rule_is_an_error`, `test_a_rule_of_a_foreign_package_is_an_error`, `test_an_attribute_of_the_report_cannot_be_required`, `test_a_type_which_names_nothing_is_an_error`, `test_an_unused_data_type_is_an_error`, `test_required_is_demanded_for_an_attribute_of_a_specification`, `test_an_unknown_key_of_a_data_type_is_an_error`. Example:

```python
def test_an_unknown_rule_is_an_error(tmp_path: Path) -> None:
    root = _repository(
        tmp_path,
        extra_glossary=_attribute("Species", "extra", 'required = false\nrules = [99999]'),
    )
    glossary = Glossary.from_directory(root / "glossary")
    with pytest.raises(GlossaryError, match=r"extra\.toml: types\.Species\.attributes\.extra.*99999"):
        glossary.validate_technical()
```

with a helper `_attribute(type_name, name, body)` which writes a complete attribute table (label, type, spec, summary, description) plus the body; add it next to `_repository` and add the schema property the coverage check needs where a test runs `--check`.
- [ ] **Step 3: Run them, they fail.** `uv run pytest tests/test_glossary.py -q -k "technical or required or rule or data_type or names_nothing"`.
- [ ] **Step 4: Implement** the parsing, `type_key`, `resolved_rules` and the three validations.
- [ ] **Step 5: The checks of `main`.** Add `validate_technical` to the checks of `main`, not yet `validate_types` and `validate_required`; the tests call these two directly.
- [ ] **Step 6: Green.** `uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run python -m sbml4humans.glossary --check`.
- [ ] **Step 7: Commit.** `git commit -m "Read the technical details of the glossary: required, default, rules and the data types"`

---

### Task 3: Write `glossary-details.json`

**Files:**
- Modify: `backend/sbml4humans/glossary.py` (new `DETAILS_PATH`, `entry_key`, `_link_keys`, `rewrite_links`, `render_details`; `_files`)
- Test: `backend/tests/test_glossary.py`
- Generated: `frontend/src/data/glossary-details.json`

**Interfaces:**
- Consumes: Task 2.
- Produces: `DETAILS_PATH = Path("frontend/src/data/glossary-details.json")`, `DOCS_URL = "https://matthiaskoenig.github.io/sbml4humans/"` (read from `site_url` of `zensical.toml` is not possible in `render_details` without the root, so a constant, asserted equal to `site_url` by a test of the repository), `render_details(glossary: Glossary) -> dict[str, Any]`.

The json: `{"entries": {key: entry}}`, keys sorted, written like `glossary.json` (`indent=2, ensure_ascii=False`, trailing newline). An entry, fields with no value left out:

```json
"types/Species/initialAmount": {
  "kind": "attribute",
  "label": "initialAmount",
  "summary": "...",
  "description": "... [compartment](glossary:types/Compartment) ...",
  "package": "core",
  "docs": "reference/species/#initialamount",
  "owner": "types/Species",
  "type": {"label": "double", "key": "datatypes/double"},
  "spec": {"label": "core 4.6.4", "section": "4.6.4", "url": "https://sbml.org/..."},
  "required": false,
  "default": "set by an initial assignment or a rule",
  "rules": [{"id": 20609, "severity": "error", "message": "...", "section": "L3V2 Section 4.6.4"}]
}
```

A type adds `"attributes": [keys in the order of the glossary]` and `"related": [keys]`; a data type `"values"`. `kind` is `type`, `attribute`, `link`, `concept` or `datatype`. `spec.label` is what `_spec_link` shows (`core 4.6.4`). `docs` is the directory url of zensical: `reference/<slug>/`, with `#<anchor>` from `_entry_anchors` for an attribute, `reference/links/#<anchor(label)>`, `reference/concepts/#...`, `reference/datatypes/#...`.

Links: `_link_keys(glossary) -> dict[str, dict[str, str]]` maps page name, then anchor (`""` for the page itself) to a key: a type page to `types/<Key>`, its attribute anchors (the same `_entry_anchors` call as `render_type_page`, so factor that call into `_type_page_anchors(entry)`) to `types/<Key>/<name>`, its heading anchors to the type; `links.md`, `concepts.md`, `datatypes.md` anchors to their entries. `rewrite_links(description, home, keys)` replaces the target of every `_LINK` match: external stays; `../page.md#a` becomes `f"{DOCS_URL}page/#a"` (`index.md` becomes the root); a page without a key of its own (`index.md`, the bare `links.md`, `concepts.md`, `datatypes.md`) becomes its absolute docs url; an unresolvable reference target raises `GlossaryError` naming entry and link. Images are untouched (`_LINK` excludes them).

- [ ] **Step 1: Failing tests:** `test_the_details_carry_the_technical_details` (the fixture entry above, field by field), `test_a_type_lists_its_attributes_and_related_types`, `test_the_details_leave_out_what_an_entry_does_not_state`, `test_a_page_link_becomes_a_glossary_link`, `test_an_anchor_link_becomes_the_key_of_the_attribute`, `test_a_link_to_a_page_of_the_site_becomes_absolute`, `test_an_external_link_stays`, `test_every_key_of_the_details_resolves` (owner, type.key, related, attributes and every `glossary:` target of the repository glossary are entries), `test_the_details_are_deterministic` (two renders dump to equal strings), `test_check_reports_stale_details`, `test_the_json_of_the_tooltips_is_unchanged` (render_json of the fixture has exactly the keys label, summary, package, page, attributes and no new one), `test_the_docs_url_is_the_url_of_the_site`.
- [ ] **Step 2: Run, fail. Step 3: Implement. Step 4:** `uv run python -m sbml4humans.glossary` and check `git diff --stat frontend/src/data/glossary.json` is empty. **Step 5:** full backend checks green. **Step 6: Commit** generator, tests and the generated json: `"Write the details of the glossary for the help dialog"`.

---

### Task 4: The technical details on the reference pages

**Files:**
- Modify: `backend/sbml4humans/glossary.py` (`_attribute_rows`, `_attribute_details`, `render_type_page`, new `DATATYPES_PAGE`, `render_datatypes_page`, `pages`, `page_of`, `_reference_pages`, `render_index_page`), `zensical.toml` (nav: `{ "Data types" = "reference/datatypes.md" }` after the overview)
- Test: `backend/tests/test_glossary.py`
- Generated: `docs/reference/*.md`

**Interfaces:**
- Produces: the attribute table `| attribute | type | required | meaning | specification |` (`required`, `optional`, `-`); after the description of an attribute `Default: <default>.` as a paragraph of its own and, when it has rules, a list `- \`20609\` (error): message`; on a type page a section `## Validation rules` before `## Related elements` (add the heading to `PAGE_HEADINGS`); a `type` cell links its data type (`[\`double\`](datatypes.md#double)`) or its type page; `datatypes.md` with one `##` section per data type: sentence, description, values as a list of code literals, the specification line.

- [ ] Tests first (`test_the_attribute_table_states_required`, `test_an_attribute_states_its_default_and_its_rules`, `test_a_type_page_lists_its_rules`, `test_the_type_of_an_attribute_links_its_data_type`, `test_renders_the_page_of_the_data_types`, and the existing navigation test extended to `datatypes.md`), run, implement, regenerate, `--check`, then build the site: `uv run --project backend zensical build --clean --strict` from the root, expected to pass without a warning. Look at one generated page in `zensical serve` and check the table is not too wide.
- [ ] Commit: `"Show required, default, validation rules and data types in the reference"`.

---

### Tasks 5 to 8: The content, one task per file section

Task 5 core (`glossary/core.toml`), Task 6 comp, Task 7 fbc, Task 8 qual and distrib (`glossary/packages.toml`, one agent at a time per file to avoid edit conflicts: 6, 7, 8 run one after the other, 5 runs in parallel to them) and, inside Task 5, the `datatypes` of core and of the report; the package tasks add the data types of their package (`PortSIdRef`, the enumerations with their `values`).

**Sources, the only ones:** the specification pdfs behind the `[specs.*]` urls of the glossary (fetch them; core L3V2 release 2, comp V1 release 3, fbc V3 release 1, qual V1 release 1, distrib V1 release 1) and libsbml for the rules. Never from memory.

**Per attribute which cites a `spec`:**
1. `required`: from the definition of the attribute in the cited section (the UML figure and the text; "required", "mandatory" against "optional").
2. `default`, only where absence means something a reader should know: Level 3 has no defaults, so this is what holds instead: inherited from the model (`substanceUnits`), set by other constructs (`initialAmount`), "undefined" is not worth stating alone.
3. `rules`: list candidates with

```python
import libsbml  # run from backend/ with `uv run python`
for code in range(20600, 20700):
    error = libsbml.SBMLError(code, 3, 2)
    if error.getMessage().strip():
        print(code, error.getSeverityAsString(), " ".join(error.getMessage().split()))
```

(the blocks of core: 20200 model, 20300 function definition, 20400 unit definition, 20500 compartment, 20600 species, 20700 parameter, 20800 initial assignment, 20900 rules, 21000 constraint, 21100 reaction and species reference, 21200 event and its children, 10500 units, 10700 SBO, 10300 identifiers; a package through the table of its extension as in `glossaryrules.py`) and cite a rule at the attribute it constrains. A rule about several attributes (20609) is cited at each of them. A rule about the element as a whole (allowed attributes, allowed children, exactly one list) is cited at the type. Do not cite rules which are "not applicable" in every version the report reads, and no SBO rule at anything but `sbo`.

**Per `type` value without an entry:** a `datatypes` entry. For a type of a specification: `spec` with the section (core 3.1.x), a one sentence summary, a description which says the syntax, what it may reference (the namespace of `SId`, of `UnitSId`, of `PortSId`) and what the report does with it. For a value type of the report (`list`, `latex`, `Math`, the fbc and comp extension objects): no `spec`, `package = "report"`.

**Second pass, by another agent, without reading the first result's reasoning:** derive `required` for every attribute of the package again from the specification and list, per cited rule, the attributes its message names; diff against the file; every difference is resolved by quoting the sentence of the specification in the report of the task.

**Gate per task:** `uv run python -m sbml4humans.glossary && uv run python -m sbml4humans.glossary --check && uv run pytest tests/test_glossary.py -q`; commit the toml with the regenerated outputs: `"State required, default and the validation rules of <package>"`.

### Task 9: Demand the content

- [ ] Add `validate_types` and `validate_required` to the checks of `main` and to `test_coverage_accepts_the_glossary_of_the_repository` style tests (`test_the_repository_states_required_everywhere`, `test_every_type_of_the_repository_resolves`). Update the module docstring of `glossary.py` (three outputs, the new checks) and the header comment of `glossary/core.toml` (the new keys, how to find a rule number). `--check` green, site build green. Commit: `"Demand required and a resolvable type for every attribute of a specification"`.

---

### Task 10: Keys, details and `help` in the view state

**Files:**
- Modify: `frontend/src/report/glossary.ts`, `frontend/src/report/query.ts`, `frontend/src/report/view.ts`
- Create: `frontend/src/report/glossaryDetails.ts`
- Test: `frontend/tests/unit/glossary.test.ts`, `query.test.ts`, new `glossaryDetails.test.ts`; fix `reportPage.test.ts` and every `toEqual` on a parsed view state

**Interfaces (produced):**

```ts
// glossary.ts
export function typeKey(type: SbmlType): string | undefined;          // "types/Species"
export function attributeKey(type: SbmlType, field: string): string | undefined; // "types/SBase/id"
export function linkKey(kind: EdgeKind): string | undefined;          // "links/compartment"
export function conceptKey(key: string): string | undefined;
/** Label and summary of any key, from the eager glossary: the header of the dialog while the details load. */
export function entryOfKey(key: string): GlossaryEntry | undefined;

// glossaryDetails.ts
export type HelpKind = "type" | "attribute" | "link" | "concept" | "datatype";
export interface HelpRule { id: number; severity: "error" | "warning"; message: string; section?: string }
export interface HelpEntry {
  kind: HelpKind; label: string; summary: string; description: string; package: string; docs: string;
  owner?: string; type?: { label: string; key: string };
  spec?: { label: string; section?: string; url: string };
  required?: boolean; default?: string; values?: string[]; rules?: HelpRule[];
  related?: string[]; attributes?: string[];
}
export interface GlossaryDetails { entries: Record<string, HelpEntry> }
export function loadGlossaryDetails(): Promise<GlossaryDetails>;

// query.ts: ViewState gains `help: string | null`, query parameter `help`
// view.ts
openHelp(key: string): Promise<unknown>;   // push
closeHelp(): Promise<unknown>;             // push, removes help
helpRoute(key: string): RouteLocationRaw;  // the href of an in-dialog link
```

`attributeEntry` and `attributeKey` share one private `resolveAttribute(type, field): { owner: string; name: string; entry: GlossaryEntry } | undefined` with today's chain. `entryOfKey` does not cover data types (the eager json has none): the dialog header falls back to the last segment of the key. `loadGlossaryDetails` caches the promise of `import("@/data/glossary-details.json")` and resets the cache when it rejects. `setEntry` and `setModel` keep `help: null`; `routeFor` across entries sets `help: null`.

- [ ] Tests first: for every type of `TYPES` and every field of `COLUMNS` and of the static `field=` of the attribute components (reuse the extractors of `glossary.test.ts`), `attributeKey` is a key of the details json (read the json with `readFileSync`, not through the loader); `typeKey`, `linkKey` for every `EDGE_KINDS`; every `owner`, `type.key`, `related`, `attributes` and `glossary:` target inside the details resolves; `help` round-trips and an empty `help` is dropped; `loadGlossaryDetails` returns the same promise twice. Run, fail, implement, `npm run lint && npm run typecheck && npm run test:unit`. Commit: `"Give every glossary entry a key and the report page the help parameter"`.

---

### Task 11: Render the markdown of a description

**Files:**
- Create: `frontend/src/report/helpMarkdown.ts`, `frontend/src/components/help/HelpMarkdown.vue`
- Modify: `frontend/package.json`, `package-lock.json` (`npm install markdown-it && npm install -D @types/markdown-it`; check `npm view markdown-it license` says MIT)
- Test: `frontend/tests/unit/helpMarkdown.test.ts`

**Interfaces:** `renderHelpMarkdown(markdown: string, hrefOf: (key: string) => string): string` (sanitised html; a `glossary:KEY` link becomes `<a href="hrefOf(KEY)" data-help-key="KEY" class="help-link">`, any other link gets `target="_blank" rel="noopener"`). `HelpMarkdown.vue`: props `{ markdown: string }`, emits `navigate(key: string)`; it renders with `v-html`, resolves `hrefOf` with `router.resolve(view.helpRoute(key)).href`, and one click listener on its root calls `preventDefault()` and emits for a plain left click on `a[data-help-key]` (a click with a modifier key keeps the browser behaviour, so the entry opens in a new tab).

`markdown-it` options: `{ html: false, linkify: false, typographer: false }`; its default `validateLink` refuses unknown schemes, so override it to also accept `glossary:` (`const ok = md.validateLink; md.validateLink = (url) => url.startsWith("glossary:") || ok(url)`). Rewrite the links in the `link_open` renderer rule. DOMPurify like `report/notes.ts` (read it first and follow it), allowing `data-help-key`, `target`, `rel`. Style the html with a scoped `:deep()` block in `HelpMarkdown.vue`: paragraphs `mb-3 leading-relaxed`, `code` in the mono style of the app (`font-mono text-[0.85em] bg-gray-100 rounded px-1`), lists, links in `text-link`.

- [ ] Tests first (glossary link, external link, raw `<script>` and `<img onerror>` in the markdown do not reach the html, inline code, a list, a `javascript:` link is dropped), fail, implement, green, commit with the lock: `"Render the descriptions of the glossary as sanitised markdown"`.

---

### Task 12: The dialog

**Files:**
- Create: `frontend/src/components/help/HelpDialog.vue`
- Modify: `frontend/src/pages/ReportPage.vue` (mount `<HelpDialog />` once inside the `report-page` element)
- Test: `frontend/tests/unit/helpDialog.test.ts`

**Interfaces:** no props; reads `useReportView().state.value.help`, loads with `loadGlossaryDetails()`, navigates with `openHelp`, closes with `closeHelp`. `HelpMarkdown` and with it `markdown-it` are imported with `defineAsyncComponent(() => import("./HelpMarkdown.vue"))`.

Behaviour: a native `<dialog data-testid="help-dialog">`; a watcher on `help` calls `showModal()` when a key arrives and the dialog is closed and `close()` when it leaves; the `close` event of the dialog (Escape) calls `closeHelp()` when `help` is still set; `@click` on the dialog element itself (the backdrop, `event.target === dialog`) closes. A key which is no entry of the loaded details calls `closeHelp()` with `replace`. jsdom has no `showModal`: the test stubs `HTMLDialogElement.prototype.showModal` and `close`.

Layout (Tailwind, the grays and `text-link` of the app): `w-full max-w-2xl max-h-[80vh] rounded-lg p-0 shadow-xl backdrop:bg-gray-900/40`, inside a flex column: header (`h-12 border-b px-4`, breadcrumb, badges, close button with `XIcon` and `aria-label="close"`), body (`overflow-y-auto px-4 py-3`), footer (`border-t px-4 py-2 text-xs`). Test ids: `help-breadcrumb`, `help-owner`, `help-title`, `help-type-badge`, `help-required-badge`, `help-close`, `help-summary`, `help-overview`, `help-technical`, `help-rules`, `help-rule`, `help-attributes`, `help-attribute-row`, `help-related`, `help-docs-link`, `help-skeleton`, `help-fallback`. Every in-dialog navigation is an `<a :href>` of `helpRoute(key)` handled like the markdown links, so that it is a real link. Section headings of the body are small caps gray labels, the rules show the number in mono, a severity mark (`CircleAlertIcon` red for an error, `TriangleAlertIcon` amber for a warning, each with an `aria-label`) and the message; `<species>` in a message is text, never html. The attributes table of a type ends with a row which opens `types/SBase` ("the common attributes of SBase" is glossary text: use the label and the summary of the `SBase` entry).

- [ ] Tests first with `vi.mock("@/report/glossaryDetails")`: a type entry, an attribute entry, no empty parts, skeleton while the promise is pending, fallback when it rejects, an unknown key closes, a click on an attribute row pushes `help`. Implement, then look at it in the dev server (`npm run dev` with the backend up) on `Species`, `Model` (30+ attributes), `types/Species/initialAmount`, a comp entry, a data type, at 1440 and at 380 pixels wide, keyboard only. Fix what looks off. Commit: `"Explain an entry of the glossary in a help dialog"`.

---

### Task 13: The entry points

**Files:**
- Create: `frontend/src/components/help/HelpLabel.vue`, `HelpButton.vue`
- Modify: `AttributeRow.vue`, `InspectorPanel.vue`, `LinksColumn.vue`, `NestedTable.vue`, `ElementTable.vue`, `ElementSection.vue`
- Test: `frontend/tests/unit/helpLabel.test.ts`, the existing `inspector.test.ts` (the `inspector-type-link` tests move to the dialog footer), `elementTable.test.ts`

**Interfaces:** `HelpLabel`: props `{ helpKey?: string; tooltip?: string }`, default slot = the label; with a key a `<button type="button" data-testid="help-label">` (`cursor-help decoration-dotted underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-link`, `text-left`, inherits font and colour, `truncate` stays with the parent), click `openHelp(key)`; without a key a `<span>`; both carry `v-tooltip.bottom="tooltip"`. `HelpButton`: props `{ helpKey: string; label: string }`, a `CircleHelpIcon` button `size-3.5 text-gray-400 hover:text-link`, `aria-label` = `` `explain ${label}` `` is a name of the frontend's own: instead use the label of the entry alone as `aria-label` and `data-testid="help-button"`; `@click.stop`.

Places: `AttributeRow` `dt` wraps its name in `HelpLabel` (`attributeKey(type, field)`), a row with a `label` prop and no field stays plain. `InspectorPanel` header: the `a[inspector-type-link]` becomes a `HelpLabel` with `typeKey`, `ExternalLinkIcon` goes; `referenceUrl` stays exported only if still used, else remove it and its test. `LinksColumn` both `dt`. `NestedTable` header span. `ElementTable` `th`: `group/th`, the `HelpButton` after the sort button, `opacity-0 group-hover/th:opacity-100 group-focus-within/th:opacity-100 focus-visible:opacity-100`, and the header must not change its width when the button appears (the button takes its space always). `ElementSection` `h2`: `HelpButton` after the type name.

- [ ] Tests first, implement one place at a time with its test, run the whole unit suite, look at every place in the dev server (hover, focus ring, truncation of long labels such as `fbc:geneProductAssociation`, no layout shift in the table header). Commit: `"Open the help dialog from the labels of the report"`.

---

### Task 14: End to end, screenshots, documentation, release notes

**Files:**
- Create: `frontend/tests/e2e/help.spec.ts`, `release-notes/0.7.0.md`
- Modify: `frontend/tests/e2e/report.spec.ts` (the `inspector-type-link` assertion at line 198 follows the link into the dialog footer), `frontend/scripts/screenshots.mjs`, `docs/images/`, `docs/report.md`, `docs/development.md`, `CLAUDE.md`

- [ ] `help.spec.ts`, against the example of the repressilator (`openExample` of `helpers.ts`; find its id in `tests/fixtures/examples.json`), one `test` per bullet of the spec's Playwright list. The lazy load: collect `page.on("request")` urls, assert none contains `glossary-details` before the first click and one does after (in the dev server the chunk is requested by its file name). Focus return: `await expect(label).toBeFocused()` after Escape.
- [ ] Run the whole e2e suite with the backend up: `npm run test:e2e`. Every spec green, no flake in two runs.
- [ ] `screenshots.mjs`: a shot `help-dialog.png` of `types/Species/initialAmount`; retake the shots which show the inspector header or clickable labels and compare old and new by eye.
- [ ] `docs/report.md`: the section "Explanations" (hover, click, badges, rules, the `help` parameter) with the screenshot. `docs/development.md`: the glossary keys `required`, `default`, `rules`, `values`, `datatypes`, the rule lookup script. `CLAUDE.md`: the glossary paragraph (three outputs, `glossaryrules.py`, the new checks), the `frontend/src` paragraph (`components/help/`, `glossaryDetails.ts`, `helpMarkdown.ts`, `help` in the view state), `markdown-it` in the dependency list.
- [ ] `release-notes/0.7.0.md` in the style of `release-notes/0.6.2.md` (read it first). No version bump.
- [ ] Everything green: backend `pytest`, `ruff`, `ty`, glossary and release notes checks (the latter may demand notes for the current version only: run `uv run python -m sbml4humans.releasenotes --check` and regenerate `docs/release-notes.md` if the new file changes it), site build strict, frontend lint, typecheck, unit, build, e2e.
- [ ] Commit, push with the gh credential helper, open the pull request against `develop` with `Closes #49`.
