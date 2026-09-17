# Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Zensical documentation site for sbml4humans with a reference generated from one glossary, and a report which explains its element types, attributes and links through tooltips and links into that reference.

**Architecture:** `glossary/*.toml` is the only place an explanation is written. `backend/sbml4humans/glossary.py` generates `frontend/src/data/glossary.json` for the application and `docs/reference/*.md` for the site from it, validates the coverage and the links, and fails the `docs` job when the committed files are stale. The site is built with Zensical from `docs/` and deployed to GitHub Pages from `develop`. The README shrinks to the motivation, the repository documentation moves into `docs/development.md` and `docs/deployment.md`.

**Tech Stack:** python 3.14 with `tomllib` (no new backend dependency) and `zensical` in the dev group of `backend/pyproject.toml`; node 24, Vue 3.5, Vitest and Playwright in `frontend/`; GitHub Actions; the repository rulesets in `.github/rulesets/`.

**Spec:** `docs/superpowers/specs/2026-09-17-documentation-design.md`

## Global Constraints

- Work in the worktree `/tmp/claude-1000/-home-mkoenig-git-sbml4humans/d5bdb9bb-738c-4934-9cd0-54022bb5ade4/scratchpad/wt-docs` on the branch `documentation`, which starts at the release 0.3.0 of `develop`.
- node 24: prefix every shell command with `export PATH=/tmp/claude-1000/-home-mkoenig-git-sbml4humans/d5bdb9bb-738c-4934-9cd0-54022bb5ade4/scratchpad/node24/bin:$PATH` and run `npm`/`npx` in `frontend/`. Run `uv` commands in `backend/`, except `zensical`, which runs from the repository root as `uv run --project backend zensical ...`.
- The shell cwd resets between commands: start every command with `cd <the directory you need>`.
- Markdown carries no hard line wraps: a paragraph, a list item or a table row is a single line, the wrapping is left to the editor. Code fences, headings and rows of badges keep their line structure.
- No em dash character anywhere. Comments and prose are full sentences in the voice of the existing code and documentation.
- Documentation prose is factual and cites its source; every claim about SBML comes from the specification, the Keating paper or the package specifications named in the spec, and the page links to them.
- Commit messages: one descriptive sentence, no conventional prefix, no `Co-Authored-By`, and a last line `Claude-Session: https://claude.ai/code/session_01H6NLTR8e7djzBnAwwiXkiU` after a blank line. Do not push; the controller pushes.
- Before every commit: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest`, and for frontend changes `cd frontend && npx prettier --write <files> && npm run lint && npm run typecheck && npx vitest run`.
- The application keeps its behaviour and its look: tooltips and two links are added, nothing else changes.
- The local SBML specification sources are at `/home/mkoenig/git/sbml-specifications` (read only, never modify): core L3V2 in `sbml-level-3/version-2/core/spec/` (`components.tex`, `preliminary.tex`), comp in `sbml-level-3/version-1/comp/spec/syntax.tex`, fbc in `sbml-level-3/version-1/fbc/spec/syntax.tex`, distrib in `sbml-level-3/version-1/distrib/sbml-level-3-distrib-package-proposal.tex`.

---

### Task 1: Zensical site, workflow and required check

**Files:**
- Create: `zensical.toml`, `docs/index.md`, `docs/development.md`, `docs/deployment.md`, `docs/references.md`, `docs/images/.gitkeep`, `.github/workflows/docs.yml`
- Modify: `backend/pyproject.toml` (dev group), `.gitignore` (site), `.github/rulesets/develop.json`
- Delete: `deploy.md`

**Interfaces:**
- Produces: a buildable site with the navigation of the spec (pages which later tasks fill), the `docs` check of the workflow, and `uv run --project backend zensical build --clean` as the build command.

- [ ] **Step 1: Add the dependency and the ignore**

In `backend/pyproject.toml` add `"zensical>=0.0.60"` to `[dependency-groups] dev`. Run `cd backend && uv sync` and commit the updated `backend/uv.lock` with the change. Add `site/` to the `.gitignore` of the repository root.

- [ ] **Step 2: Write `zensical.toml`**

Follow `/home/mkoenig/git/sbmlutils/zensical.toml`: same `[project.theme]` features and palette (`primary = "teal"`, `accent = "teal"`), the same `[project.markdown_extensions]`, and `[[project.extra.social]]` with the GitHub link. Values for this repository:

```toml
[project]
site_name = "sbml4humans"
site_url = "https://matthiaskoenig.github.io/sbml4humans/"
site_description = "Interactive, human readable reports of SBML models"
site_author = "Matthias König"

copyright = 'Copyright &copy; 2021-2026 <a href="https://livermetabolism.com">Matthias König</a>'

repo_url = "https://github.com/matthiaskoenig/sbml4humans"
repo_name = "matthiaskoenig/sbml4humans"
edit_uri = "edit/develop/docs/"

nav = [
  { "Home" = "index.md" },
  { "SBML" = "sbml.md" },
  { "User guide" = [
    { "Loading a model" = "inputs.md" },
    { "Reading a report" = "report.md" },
  ] },
  { "Reference" = [
    { "Overview" = "reference/index.md" },
    { "Links between elements" = "reference/links.md" },
    { "Report concepts" = "reference/concepts.md" },
  ] },
  { "References" = "references.md" },
  { "Development" = [
    { "Development" = "development.md" },
    { "Deployment" = "deployment.md" },
  ] },
]
```

The per type reference pages are added to the navigation in Task 3, when the generator writes them.

- [ ] **Step 3: Create the pages this task owns**

- `docs/index.md`: for now the title `# sbml4humans`, one sentence from the README ("[SBML4Humans](https://sbml4humans.de) renders [SBML](https://sbml.org) models as interactive, human readable reports.") and a "The documentation is being written." line. Task 5 writes the real page.
- `docs/development.md`: move the development content of `README.md` (repository layout, the docker compose setup, the backend section, the frontend section, "Branches and pull requests" and "Releases") into it, unchanged in wording except that references to "this README" become references to the page, and add a "Documentation" section describing `uv run --project backend zensical serve` (live preview), `uv run --project backend zensical build --clean` (build into `site/`), where the sources live and that `python -m sbml4humans.glossary` regenerates the reference (Task 2 adds the command, describe it as the plan states).
- `docs/deployment.md`: the content of `deploy.md`, with the headings kept and the prose lightly corrected where it is ungrammatical. Delete `deploy.md` and point the places which linked to it (`README.md`, `CLAUDE.md`) at `docs/deployment.md`.
- `docs/references.md`: the citations of the spec section of the design document, each with its doi or url: the SBML L3V2 core specification, Keating et al. 2020, MIRIAM, SBO, identifiers.org, the COMBINE archive specification, the Google Summer of Code project with the NRNB issue and the project blog.
- `docs/images/.gitkeep`: an empty file so the directory exists.

`README.md` keeps everything else for now; Task 7 shrinks it.

- [ ] **Step 4: Add the workflow**

`.github/workflows/docs.yml`, modelled on `/home/mkoenig/git/sbmlutils/.github/workflows/docs.yml`: name `documentation`, triggers `push` to `[develop, main]`, `pull_request` to `[develop, main]`, `workflow_dispatch`, concurrency per pull request with `cancel-in-progress: false`, `permissions: contents: read`. Job `docs` (with `name: docs` and the comment that the branch protection requires it): checkout with `persist-credentials: false`, `actions/configure-pages@v6`, `astral-sh/setup-uv@v10.0.1` with python 3.14 and cache, `uv sync` in `backend` (the dev group is installed by default), then from the repository root `uv run --project backend zensical build --clean`, then `actions/upload-pages-artifact@v5` with `path: site`. Job `deploy`: `needs: docs`, `if: github.ref == 'refs/heads/develop'`, permissions `pages: write` and `id-token: write`, environment `github-pages`, `actions/deploy-pages@v5`. Task 2 adds the `--check` step before the build.

- [ ] **Step 5: Require the check**

Add `{ "context": "docs" }` to the `required_status_checks` of `.github/rulesets/develop.json`, after `ty`. Do not run `apply.sh` (the controller applies it after the merge).

- [ ] **Step 6: Build and commit**

```bash
cd backend && uv sync
cd /tmp/claude-1000/-home-mkoenig-git-sbml4humans/d5bdb9bb-738c-4934-9cd0-54022bb5ade4/scratchpad/wt-docs && uv run --project backend zensical build --clean
ls site/index.html
git add -A zensical.toml docs .github backend/pyproject.toml backend/uv.lock .gitignore README.md CLAUDE.md
git rm deploy.md
git commit -m "..."
```

Expected: the build writes `site/`, `site/` is not tracked by git, and the navigation shows the pages of this task (the pages of later tasks are added with them).

---

### Task 2: The glossary format, the generator and the core glossary

**Files:**
- Create: `glossary/core.toml`, `backend/sbml4humans/glossary.py`, `backend/tests/test_glossary.py`, `backend/tests/data/glossary/*.toml` (fixture)
- Modify: `.github/workflows/docs.yml` (the `--check` step)

**Interfaces:**
- Consumes: `frontend/src/schema/report.schema.json` (the list of types and their fields), `frontend/src/data/edgeKinds.ts` (the link kinds).
- Produces:
  - `glossary/` in the format of the design document
  - `python -m sbml4humans.glossary` writing `frontend/src/data/glossary.json`, `docs/reference/index.md`, `docs/reference/<slug>.md`, `docs/reference/links.md`, `docs/reference/concepts.md`
  - `python -m sbml4humans.glossary --check` failing on stale files, missing entries, broken links or missing images
  - the slug of a type is its name in lower case (`SpeciesReference` becomes `speciesreference.md`), the anchor of an attribute is its label with spaces replaced by dashes, in lower case

- [ ] **Step 1: Write the fixture and the failing tests**

`backend/tests/data/glossary/core.toml` with two types (one with an attribute, one without), one link kind and one concept, in the format of the design document.

`backend/tests/test_glossary.py`:

```python
"""Tests of the glossary generator."""

from pathlib import Path

import pytest

from sbml4humans.glossary import Glossary, GlossaryError, render_json, render_type_page


FIXTURE = Path(__file__).parent / "data" / "glossary"


def test_reads_the_entries() -> None:
    glossary = Glossary.from_directory(FIXTURE)
    assert glossary.types["Species"].label == "Species"
    assert glossary.types["Species"].attributes["initialAmount"].summary
    assert glossary.links["compartment"].label == "compartment"
    assert glossary.concepts["derivedUnits"].label == "derived units"


def test_renders_the_page_of_a_type() -> None:
    glossary = Glossary.from_directory(FIXTURE)
    page = render_type_page(glossary, glossary.types["Species"])
    assert page.startswith("# Species\n")
    assert "| initial amount |" in page
    assert "[Compartment](compartment.md)" in page
    assert "SBML Level 3 Version 2 Core" in page


def test_renders_the_json_without_the_descriptions() -> None:
    glossary = Glossary.from_directory(FIXTURE)
    data = render_json(glossary)
    assert data["types"]["Species"]["summary"]
    assert "description" not in data["types"]["Species"]
    assert data["types"]["Species"]["attributes"]["initialAmount"]["label"] == "initial amount"
    assert data["links"]["compartment"]["summary"]
    assert data["concepts"]["derivedUnits"]["summary"]


def test_a_missing_summary_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "core.toml").write_text('[types.Species]\nlabel = "Species"\n')
    with pytest.raises(GlossaryError, match="summary"):
        Glossary.from_directory(tmp_path)


def test_a_broken_page_link_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "core.toml").write_text(
        '[types.Species]\nlabel = "Species"\nsummary = "a species"\n'
        'description = "see [Nothing](nothing.md)"\n'
    )
    glossary = Glossary.from_directory(tmp_path)
    with pytest.raises(GlossaryError, match="nothing.md"):
        glossary.validate_links()
```

Run: `cd backend && uv run pytest tests/test_glossary.py`
Expected: FAIL, `ModuleNotFoundError: No module named 'sbml4humans.glossary'`.

- [ ] **Step 2: Implement the generator**

`backend/sbml4humans/glossary.py` with:

- dataclasses `Entry` (`key`, `label`, `summary`, `description`, `spec`, `type`, `related`, `attributes`) and `Glossary` (`specs`, `types`, `links`, `concepts`) with `Glossary.from_directory(path)` reading every `*.toml` of the directory with `tomllib`, raising `GlossaryError` with the file and the key when `label`, `summary` or `description` is missing, when a `spec` points to an unknown document, or when a `related` type does not exist.
- `render_json(glossary)` returning the dict written to `frontend/src/data/glossary.json`: `{"types": {name: {"label", "summary", "package", "page", "attributes": {field: {"label", "summary"}}}}, "links": {...}, "concepts": {...}}`, sorted by key, written with an indent of 2 and a trailing newline, so prettier and git stay quiet.
- `render_type_page(glossary, entry)` returning the markdown of a type page: `# <label>`, the summary as the first paragraph, the description, a table `| attribute | type | meaning | specification |` with one row per attribute (the specification cell links the section of the document), a "Related elements" list of links to the related pages, and a "In the report" section listing the report fields of the type (the attributes whose `package` is `report`).
- `render_index_page`, `render_links_page`, `render_concepts_page` for the three remaining pages.
- `write(glossary, root)` writing every file, and `check(root)` regenerating into a temporary directory and comparing, raising `GlossaryError` with the list of stale files.
- `validate_coverage(glossary, root)`: reads `frontend/src/schema/report.schema.json` and asserts every SBase derived definition and every property of it has an entry (the shared `SBase` attributes count for every type), and reads the `EDGE_KINDS` array of `frontend/src/data/edgeKinds.ts` and asserts every kind has an entry.
- `validate_links(glossary, root)`: every `[text](target.md)` of a description resolves to a generated page, every `![alt](images/x.png)` of a page under `docs/` exists.
- `main(argv)` with `--check`, printing what is stale or missing and exiting with 1, and without it writing the files. `python -m sbml4humans.glossary` calls it.

Write the module with full type annotations and google style docstrings, as the rest of the backend.

Run: `cd backend && uv run pytest tests/test_glossary.py`
Expected: PASS.

- [ ] **Step 3: Write the core glossary**

`glossary/core.toml` with the specification documents (`l3v2` for the core, `keating` for the paper, plus the entries the other tasks need) and the entries for:

- `SBase` with the attributes `id`, `name`, `metaId`, `sbo`, `notes`, `cvterms`, `history`, `xml`
- the types `SBMLDocument`, `Model`, `FunctionDefinition`, `UnitDefinition`, `Compartment`, `Species`, `Parameter`, `InitialAssignment`, `AssignmentRule`, `RateRule`, `AlgebraicRule`, `Constraint`, `Reaction`, `SpeciesReference`, `ModifierSpeciesReference`, `KineticLaw`, `LocalParameter`, `Event`, `EventAssignment`
- for every type every attribute the report shows, i.e. the columns of `frontend/src/report/columns/core.ts` and the rows of the matching component in `frontend/src/components/inspector/attributes/`, with the label the report uses

Write the prose from `/home/mkoenig/git/sbml-specifications/sbml-level-3/version-2/core/spec/components.tex` (class by class) and `preliminary.tex` (`SBase`); every entry names the section of the specification in its `spec` table. The summary is one sentence which reads well in a tooltip; the description is two to four sentences which explain the element to a modeller who does not know SBML, plus what the report shows for it. Do not copy the specification verbatim beyond short phrases.

- [ ] **Step 4: Generate, verify and add the check to the workflow**

```bash
cd backend && uv run python -m sbml4humans.glossary
cd .. && git status --short
```

Expected: `frontend/src/data/glossary.json` and `docs/reference/*.md` are written. Read two generated pages and confirm the tables and the links look right.

Add to `.github/workflows/docs.yml`, in the `docs` job before the build:

```yaml
      - name: Check that the generated reference is current
        run: uv run --project backend python -m sbml4humans.glossary --check
```

Run: `cd backend && uv run python -m sbml4humans.glossary --check`
Expected: exit code 0. Then change one summary by hand, run again, expect exit code 1 and the file listed; restore it.

- [ ] **Step 5: Commit**

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest
cd .. && git add glossary backend docs frontend/src/data/glossary.json .github/workflows/docs.yml
git commit -m "..."
```

---

### Task 3: The glossary of the packages, the links and the report concepts

**Files:**
- Create: `glossary/packages.toml`, `glossary/report.toml`
- Modify: `zensical.toml` (the reference pages in the navigation), the generated files

**Interfaces:**
- Consumes: the generator and the format of Task 2.
- Produces: entries for every remaining type, every link kind and every report concept, and the per type pages in the navigation.

- [ ] **Step 1: Write `glossary/packages.toml`**

The types `ExternalModelDefinition`, `Submodel`, `Port` (comp), `GeneProduct`, `Objective` (fbc) and `Uncertainty` (distrib) with their attributes as the report shows them (`frontend/src/report/columns/packages.ts` and the matching inspector components), and the package entries themselves (what comp, fbc and distrib are for). Sources: the package specifications named in the global constraints. Every entry has a `spec` pointing at the package specification, so the pages link it.

- [ ] **Step 2: Write `glossary/report.toml`**

- the 17 link kinds of `frontend/src/data/edgeKinds.ts`: `compartment`, `reactant`, `product`, `modifier`, `variable`, `symbol`, `units`, `conversionFactor`, `fluxBound`, `geneProduct`, `associatedSpecies`, `fluxObjective`, `modelRef`, `port`, `replacedBy`, `replacedElement`, `math`. Every entry says which element references which and where the report shows it ("References" or "Referenced by" of the inspector).
- the concepts `pk`, `sbmlType`, `derivedUnits`, `equation`, `math`, `unitsLatex`, `modelKind`, `manifest`: what the report computes, how it is computed (for example the derived units come from the units of the model elements, the equation from the reactants and products) and where it is shown.

- [ ] **Step 3: Generate and put the pages into the navigation**

Run the generator, then add the per type pages to the `Reference` section of `zensical.toml`, grouped as `Core`, `Hierarchical models (comp)`, `Flux balance constraints (fbc)`, `Distributions (distrib)`, each entry `{ "<label>" = "reference/<slug>.md" }`, in the order of `frontend/src/data/sbmlTypes.ts`.

- [ ] **Step 4: Verify the coverage**

Run: `cd backend && uv run python -m sbml4humans.glossary --check`
Expected: exit code 0, i.e. every type, attribute, link kind and concept of the report has an entry.

Then build the site and open two reference pages:

```bash
cd /tmp/claude-1000/-home-mkoenig-git-sbml4humans/d5bdb9bb-738c-4934-9cd0-54022bb5ade4/scratchpad/wt-docs && uv run --project backend zensical build --clean
grep -c "initial amount" site/reference/species/index.html
```

Expected: the built page of the species exists and contains the attribute table.

- [ ] **Step 5: Commit**

Same checks as Task 2, then commit.

---

### Task 4: The report explains itself

**Files:**
- Create: `frontend/src/report/glossary.ts`, `frontend/tests/unit/glossary.test.ts`
- Modify: `frontend/src/components/report/ElementTable.vue`, `frontend/src/components/inspector/AttributeRow.vue`, `frontend/src/components/inspector/LinksGroup.vue`, `frontend/src/components/misc/TypeMark.vue`, `frontend/src/components/inspector/InspectorPanel.vue`, `frontend/src/components/layout/AppBar.vue`, `frontend/.env.development`, `frontend/.env.production`, `frontend/tests/e2e/report.spec.ts`

**Interfaces:**
- Consumes: `frontend/src/data/glossary.json` (Task 2 and 3), the `v-tooltip` directive (a string value, `.bottom` and the other placement modifiers), `typeInfo` of `@/data/sbmlTypes`, `EDGE_KINDS` of `@/data/edgeKinds`.
- Produces:
  - `export interface GlossaryEntry { label: string; summary: string }`
  - `export function typeEntry(type: SbmlType): GlossaryEntry | undefined`
  - `export function attributeEntry(type: SbmlType, field: string): GlossaryEntry | undefined` (falls back to the `SBase` attributes and strips a dotted path to its first segment, so `kineticLaw.math` resolves the `math` of `KineticLaw`)
  - `export function linkEntry(kind: EdgeKind): GlossaryEntry | undefined`
  - `export const DOCS_URL: string` (the value of `import.meta.env.VITE_DOCS_URL`, falling back to `https://matthiaskoenig.github.io/sbml4humans/`, because Vitest does not load `.env.development`)
  - `export function referenceUrl(type: SbmlType, field?: string): string`

- [ ] **Step 1: Write the failing tests**

`frontend/tests/unit/glossary.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { COLUMNS } from "@/report/columns";
import { EDGE_KINDS } from "@/data/edgeKinds";
import { DOCUMENT_TYPES, ELEMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { DOCS_URL, attributeEntry, linkEntry, referenceUrl, typeEntry } from "@/report/glossary";

const TYPES = [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES];

describe("glossary", () => {
  it("has an entry for every element type", () => {
    for (const info of TYPES) expect(typeEntry(info.type), info.type).toBeDefined();
  });

  it("has an entry for every column of every table", () => {
    for (const [type, columns] of Object.entries(COLUMNS)) {
      for (const column of columns) {
        expect(attributeEntry(type as never, column.field), `${type}.${column.field}`).toBeDefined();
      }
    }
  });

  it("has an entry for every link kind", () => {
    for (const kind of EDGE_KINDS) expect(linkEntry(kind), kind).toBeDefined();
  });

  it("falls back to the shared attributes and to the first segment of a path", () => {
    expect(attributeEntry("Species", "metaId")?.label).toBe("meta id");
    expect(attributeEntry("Reaction", "kineticLaw.math")?.label).toBe("math");
  });

  it("builds the url of a reference page", () => {
    expect(referenceUrl("Species")).toBe(`${DOCS_URL}reference/species/`);
    expect(referenceUrl("Species", "initialAmount")).toBe(`${DOCS_URL}reference/species/#initial-amount`);
  });
});
```

Run: `cd frontend && npx vitest run tests/unit/glossary.test.ts`
Expected: FAIL, `Failed to resolve import "@/report/glossary"`.

- [ ] **Step 2: Implement the lookup**

`frontend/src/report/glossary.ts` imports `glossary.json` (Vite resolves a json import to the parsed object), types it with the interfaces above, and implements the four functions. `referenceUrl` builds `${DOCS_URL}reference/${type.toLowerCase()}/` with the anchor of the attribute label (lower case, spaces to dashes); `DOCS_URL` is `import.meta.env.VITE_DOCS_URL` with the default above, so the tests and a build without the variable agree. Add `VITE_DOCS_URL=https://matthiaskoenig.github.io/sbml4humans/` to `frontend/.env.development` and `frontend/.env.production`.

Run the test again. Expected: PASS.

- [ ] **Step 3: Add the tooltips**

- `ElementTable.vue`: the content of a header cell (the sort button or the plain span) gets `v-tooltip.bottom="attributeEntry(type, column.field)?.summary"`.
- `AttributeRow.vue`: the `dt` (the label) gets `v-tooltip.bottom` with the summary of the attribute; the component needs the type of the element, so it takes a new optional prop `type?: SbmlType` and `field?: string`, and the attribute components pass them where they render a row. Keep the change mechanical: every `<AttributeRow label="...">` of `frontend/src/components/inspector/attributes/*.vue` gets `:type="element.sbmlType"` and `field="<the field>"`.
- `TypeMark.vue`: the marker gets `v-tooltip.bottom="typeEntry(type)?.summary"` instead of its current `title` attribute.
- `LinksGroup.vue`: the `dt` with the label of the group gets `v-tooltip.bottom="linkEntry(kind)?.summary"`.

Write a unit test per place (a rendered table header, an attribute row, a type mark and a link group carry the summary as tooltip value) in the existing test files of those components, using the directive as the other tests do.

- [ ] **Step 4: Add the links into the documentation**

- `InspectorPanel.vue`: the type label of the header becomes an anchor to `referenceUrl(element.sbmlType)` with `target="_blank"`, `rel="noopener"`, `data-testid="inspector-type-link"` and the `ExternalLinkIcon` of `@lucide/vue` (`size-3`), styled like the other links (`text-link hover:underline`). The label itself keeps its `data-testid="inspector-type"`.
- `AppBar.vue`: a "Documentation" link next to "Examples", pointing at `import.meta.env.VITE_DOCS_URL`, `target="_blank"`, `rel="noopener"`, `data-testid="app-bar-docs"`, in the same style as the "Examples" link.

- [ ] **Step 5: End to end test**

In `frontend/tests/e2e/report.spec.ts`, inside the `repressilator` describe, add a test which opens the report, hovers the header of the `id` column of the species table and asserts the tooltip (`page.getByRole("tooltip")`) shows the summary of the `id` attribute (read the expected text from `glossary.json` in the test, so it cannot drift), and asserts the inspector type link points at the reference page of the species (`toHaveAttribute("href", /reference\/species\//)`).

- [ ] **Step 6: Verify and commit**

```bash
cd frontend && npx prettier --write src tests && npm run lint && npm run typecheck && npx vitest run && npm run build
CI=1 npx playwright test --reporter=line
```

Expected: every unit test passes, the build has no warning, every end to end test passes (the backend runs on port 1444, port 3456 is free). Then commit.

---

### Task 5: The pages of the site

**Files:**
- Modify: `docs/index.md`, `docs/references.md`
- Create: `docs/sbml.md`, `docs/inputs.md`, `docs/report.md`

**Interfaces:**
- Consumes: the reference pages of Task 3 (link them), the screenshots of Task 6 (Task 6 inserts the images, this task leaves the marked places).

- [ ] **Step 1: `docs/sbml.md`**

Sections: "What SBML is" (the exchange format for computational models, from Keating et al. 2020, with the citation), "Levels and versions" (Level 3 Version 2 Core as the current core specification, what a level and a version mean), "The structure of a model" (compartments, species, parameters, reactions with their kinetic laws, rules, initial assignments, events, function and unit definitions, each linking its reference page), "Packages" (what a Level 3 package is, the table of the packages from the Keating paper with one line each, and which ones the report supports: comp, fbc, distrib), "Annotations" (MIRIAM style annotations, cvterms with their qualifiers, resources resolved through identifiers.org, SBO terms, what the report shows), "COMBINE archives" (what an archive is, the manifest, that a report shows one entry per SBML file). Every claim cites its source, every element name links its reference page.

- [ ] **Step 2: `docs/inputs.md`**

The three inputs of the home page (upload of a file, a url, pasted content), the accepted formats (SBML xml, gzipped SBML, COMBINE archive as omex or zip), the examples page and what the examples are, what happens with an invalid model (the error of libsbml is shown), and that a report can be shared by its url (`?url=`), with the places for the screenshots of Task 6 marked by a line `<!-- screenshot: home-inputs -->` and the like.

- [ ] **Step 3: `docs/report.md`**

How to read a report: the type rail with the counts and the filter, the element tables (the columns come from the type, sorting, selecting a row opens the inspector, windowing above 200 rows), the search, the inspector with its three columns (attributes, links, annotations), the links between elements ("References" and "Referenced by", linking `reference/links.md`), notes, history and the XML view, the context bar with the archive entry and the model, and the url of a report (`pk`, `q`, `types`, `entry`, `model`). Every element type and attribute named on the page links its reference page. Mark the screenshot places as in Step 2.

- [ ] **Step 4: `docs/index.md`**

The motivation: what the application is for, in the words of the Google Summer of Code project ("a human readable interactive report which conveys the SBML information and content of a model is urgently needed", NRNB issue #164, with the link), who it is for (modellers, reviewers, students), what a report shows, a screenshot place `<!-- screenshot: report-overview -->`, the three ways to load a model linking `inputs.md`, the reference linking `reference/index.md`, and the funding note (Google Summer of Code 2021, Sankha Das with Matthias König and Ralf Steuer).

- [ ] **Step 5: Verify and commit**

```bash
cd /tmp/claude-1000/-home-mkoenig-git-sbml4humans/d5bdb9bb-738c-4934-9cd0-54022bb5ade4/scratchpad/wt-docs && uv run --project backend zensical build --clean && cd backend && uv run python -m sbml4humans.glossary --check
```

Expected: the site builds, the check passes (the links of the new pages resolve). Read the built pages of the four files and confirm the navigation, the headings and the links work. Then commit.

---

### Task 6: Screenshots

**Files:**
- Create: `frontend/scripts/screenshots.mjs`, `docs/images/*.png`
- Modify: `frontend/package.json` (the `screenshots` script), `docs/index.md`, `docs/inputs.md`, `docs/report.md` (insert the images), `docs/development.md` (how to rerun)

- [ ] **Step 1: Write the script**

`frontend/scripts/screenshots.mjs`, in the style of the e2e helpers, using `@playwright/test`'s `chromium`: it expects the dev server on http://localhost:3456 and the backend on 1444 (it does not start them, the script prints what it expects when a request fails), uses a viewport of 1600x1000 with `deviceScaleFactor: 2`, and writes these files into `docs/images/`:

| file | what it shows |
| --- | --- |
| `home-inputs.png` | the home page with the upload, url and paste tabs |
| `examples.png` | the examples page |
| `report-overview.png` | the report of the repressilator, full page |
| `report-tables.png` | the element tables with the type rail |
| `inspector-species.png` | the inspector of a species with its three columns |
| `inspector-annotations.png` | the annotations column of an element with resolved labels (use an element of `icg_body (icg_body.xml)`, which carries annotations) |
| `report-search.png` | the search with a filtered table |
| `archive-entries.png` | the entry selection of the example `CompModels` |

Every shot waits for the state it shows (locator assertions, no fixed timeouts), and the script closes the browser at the end.

- [ ] **Step 2: Add the npm script and take the screenshots**

`"screenshots": "node scripts/screenshots.mjs"` in `frontend/package.json`.

```bash
cd frontend && (nohup npx vite --port 3456 > /tmp/vite-shots.log 2>&1 &)
# wait until http://localhost:3456 answers
npm run screenshots
pkill -f "vite --port 3456"
ls -la ../docs/images/
```

Expected: the eight png files exist and show what the table says. Look at every one of them and retake it when it shows a loading state or an empty page.

- [ ] **Step 3: Insert the images**

Replace the marked places of `docs/index.md`, `docs/inputs.md` and `docs/report.md` by the images, each with an alt text which describes what is shown, for example `![The report of the repressilator model](images/report-overview.png)`. Add to `docs/development.md` a paragraph under the documentation section: the screenshots are taken with `npm run screenshots` against a running backend and dev server, and they are committed; rerun it after a change of the user interface.

- [ ] **Step 4: Verify and commit**

```bash
cd backend && uv run python -m sbml4humans.glossary --check
cd .. && uv run --project backend zensical build --clean && ls site/images/ | head
```

Expected: the check passes (every referenced image exists), the site contains the images. Then commit.

---

### Task 7: The README, CLAUDE.md and the final check

**Files:**
- Modify: `README.md`, `frontend/README.md`, `CLAUDE.md`

- [ ] **Step 1: Shrink `README.md`**

The README keeps: the title, the badges if there are any, the sentence what sbml4humans is, two or three sentences of motivation (why a human readable report, from the design document's sources), the screenshot `docs/images/report-overview.png`, a short feature list (element tables with search and filter, the inspector with attributes, links, annotations, notes and XML, math and units rendered, COMBINE archives, examples), the links to the documentation site (home, reading a report, reference, development, deployment), the funding note and the license. Everything else (repository layout, development setup, commands, branches and pull requests, releases) is already in `docs/development.md` after Task 1 and is removed here.

- [ ] **Step 2: `frontend/README.md`**

Keep the frontend specific commands and add a first line linking the documentation site and `docs/development.md`.

- [ ] **Step 3: `CLAUDE.md`**

Add to the architecture part: the glossary in `glossary/*.toml` is the single source of the explanations, `python -m sbml4humans.glossary` generates `frontend/src/data/glossary.json` and `docs/reference/`, `--check` runs in the `docs` job, the site is built with `uv run --project backend zensical build --clean` from the repository root and deployed to GitHub Pages from `develop`, and the screenshots are taken with `npm run screenshots`.

- [ ] **Step 4: Full verification**

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest && uv run python -m sbml4humans.glossary --check
cd ../frontend && npm run lint && npm run typecheck && npx vitest run && npm run build && CI=1 npx playwright test --reporter=line
cd .. && uv run --project backend zensical build --clean && grep -rn "deploy.md" README.md CLAUDE.md docs || true
```

Expected: everything passes, no reference to the deleted `deploy.md` is left.

- [ ] **Step 5: Commit**
