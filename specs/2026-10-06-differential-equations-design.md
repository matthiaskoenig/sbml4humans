# Differential equations of a model (issue #5): design

## Goal

Issue #5 asks to see the differential equations of a model in its report, the rates of change of the species written with the fluxes of the reactions. The report gets a second view next to the tables, "Equations", which shows the complete mathematical model of a document: the ODE system, the reaction rates, the assignment rules, the function definitions, the initial values and the events, typeset with KaTeX. Every symbol of an equation links to its element in the inspector, the inspector of an element shows its own equation, and the system can be downloaded as code (python, julia, R) or as a document (LaTeX, typst, markdown).

Success: a modeler opens a report, switches to "Equations" and reads the ODE system of the model as it would be written in a paper, with the division by the volume of a compartment, conversion factors and events stated, and with every symbol one click away from its element.

## Decisions

- **The analysis is the one of sbmlutils.** sbmlutils 0.14.0 has an ODE export (`sbmlutils.converters.ode`) with a typed intermediate model, `OdeSystem`, which resolves amounts and concentrations, conversion factors, rate rules, assignment rules in the order of their dependencies, and events with the rescaling of a resized compartment. It is not written a second time.
- **It moves into a package of its own, `sbmlode`** (repository `matthiaskoenig/sbmlode`, PyPI `sbmlode`, its publisher configured), which depends on python-libsbml and jinja2 only. sbmlutils depends on it and keeps `sbmlutils.converters.ode` as a re-export, sbml4humans depends on it. The rule of `CLAUDE.md`, no dependency on an SBML model building library, holds: sbmlode reads and prints, it builds no model. The sentence is extended to say so.
- **No HTML target.** An HTML rendering of the system would bypass the typed report, the glossary, the link graph and the inspector. sbmlode gets a **typed target** instead: `OdeSystem.typeset(...)` returns the typeset system as frozen dataclasses, the templates of the document formats render these, and sbml4humans maps them into its report model.
- **Links are a hook, not KaTeX in sbmlode.** `typeset` takes `wrap(symbol, typeset) -> str`, called for every symbol it writes. sbml4humans wraps a symbol as `\htmlData{pk=<pk>}{<typeset>}`, which KaTeX renders as an element with `data-pk`. The backend states the pk, the frontend never builds one.
- **Placement: a view switch "Tables | Equations"** at the start of the type bar, chosen in the prototype `.lavish/issue-5-odes.html`. The equations take the place of the tables, the inspector stays.
- **The inspector shows the equation of its element** (a species, a reaction, a rule's variable, a parameter or compartment with an equation), with a link to its row in the view.
- **The search switches to the tables.** Typing a search while the equations are shown switches the view to the tables. Filtering equation rows is not in this version.
- Symbols are typeset from ids (`tau_mRNA` as τ<sub>mRNA</sub>), never from names: a name is free text and would have to be escaped into math, and ids are what the tables show. The name of an element is the tooltip of its symbol.

## Part 1: sbmlode

### Extraction

The repository `matthiaskoenig/sbmlode` exists with a README only. The code of sbmlutils moves into it with its history (`git filter-repo` on a clone of sbmlutils, keeping the paths below and renaming `sbmlutils/converters/ode` to `sbmlode`):

- `src/sbmlutils/converters/ode/` to `src/sbmlode/`,
- `src/sbmlutils/resources/converters/ode/` (the templates) to `src/sbmlode/templates/`,
- `tests/converters/ode/` (with `golden/`, `docker/`, `julia/`) to `tests/`,
- `docs/ode.md`, `docs/api/converters.ode.md`, `docs/images/ode/`, the spec and plan of the ODE export to `docs/`.

The three imports of sbmlutils outside the package are replaced:

- `sbmlutils.io.sbml.read_sbml`: by `libsbml.readSBMLFromFile` / `readSBMLFromString` with the same error handling (`ValueError` for a document with errors).
- `sbmlutils.comp.flatten.flatten_sbml_doc`: by libsbml's `CompFlatteningConverter` with the options sbmlutils sets; the comp tests of the ODE export prove it unchanged.
- `sbmlutils.report.units.udef_to_string`: by a module `sbmlode.units` with the string of a unit definition, the part of sbmlutils' function the export uses, with its tests.

`sbmlutils.__version__` in the generated code and documents becomes `sbmlode.__version__` ("written by sbmlode 0.1.0"); the golden files change in this line only.

The models of the tests which come from sbmlutils' resources (the SBML test suite, the repressilator, the demo models) are copied into `tests/data/` where they are small; the SBML test suite (56 MB) is downloaded by the test of the test suite into a cache directory and the test is skipped offline, as `sbmlutils.biomodels` does.

### Project

sbmlode is set up as sbmlutils and sbml4humans are, from their files, adapted and not reinvented:

- **Packaging:** `pyproject.toml` (hatchling, src layout), uv with a committed `uv.lock`, the python versions of sbmlutils (3.11 to 3.15), `tox.ini` with the envs of the python versions, `lowest` (the lowest versions of the dependencies, `lowest-overrides.txt`) and `ty`, plus the ODE envs moved from sbmlutils (`julia`, `r`, `latex`, the docker tests), MIT `LICENSE`, `README.md`, `CITATION.cff` and `.zenodo.json`.
- **Code quality:** ruff with the rule set of sbmlutils (google docstrings, isort, pyupgrade, bugbear, lazy logging), ty with `error-on-warning = true`, every module, class and function annotated and documented; the workflows `ruff.yml` and `ty.yml`.
- **CI/CD:** `ci-cd.yml` with the jobs `test` (the matrix of python versions and operating systems), `tests` (the result of the matrix, the required check), `julia`, `r` and `latex` (moved from sbmlutils with their installation of julia, R with deSolve, tectonic and typst), `build`, `publish` (PyPI through the trusted publisher on a tag), `github-release` (the body from `release-notes/<version>.md`) and `sync-main`, which fast-forwards `main` to a release.
- **Documentation:** a zensical site (`zensical.toml`, `docs/`): the overview, the formats with examples (the repressilator in every format, the images of `docs/images/ode/`), the typed target and its `wrap`, the API reference, the design, the release notes generated from `release-notes/` (`sbmlode.releasenotes`, as in sbml4humans) and the development and release steps. The workflow `docs.yml` builds it strictly on every pull request and its `deploy` job publishes it from `develop` to GitHub Pages, <https://matthiaskoenig.github.io/sbmlode/>; the `github-pages` environment allows `develop`.
- **Repository rules:** `.github/rulesets/` (`develop.json`, `main.json`, `tags.json`, `tag-creation.json`, `apply.sh`) as in sbmlutils: every change of `develop` through a pull request with the required checks `tests`, `julia`, `r`, `latex`, `ruff`, `ty` and `docs`, squash or rebase merges only, `main` moved only by `sync-main`, tags neither moved nor deleted. `develop` is the default branch.
- **Releases:** bump-my-version (`tag = false`), which updates the version in `pyproject.toml`, `__init__.py`, `CITATION.cff` and regenerates the release notes as a hook; the release notes of a version are written before the bump, the tag is created on `develop` after the merge of the bump.
- **Agent instructions:** `CLAUDE.md` with the commands, the architecture (the three layers, the typed target) and the conventions.
- **Tests:** all of the heavy testing of the ODE export lives here: the numerical tests against the SBML test suite, the golden files, the generated code run with python, julia and R, the documents compiled with tectonic and typst, the safety tests.

Done by the user: enabling the Zenodo integration of the repository (for the DOI of `CITATION.cff`) and applying the rulesets with `apply.sh` if the token of the agent cannot.

### Typed target

`OdeSystem.typeset(dialect: Literal["latex", "typst"] = "latex", symbols: Literal["id", "name"] = "id", wrap: Callable[[Symbol, str], str] | None = None) -> TypesetSystem`

`TypesetSystem` and its rows are frozen dataclasses with the content `DocumentContext.build` returns today as dicts: `model`, `units`, `compartments`, `species`, `parameters`, `functions`, `initial`, `assignments`, `amounts`, `reactions`, `odes`, `events`, `unsupported`. An equation is `TypesetEquation(variable: Symbol | None, lhs: str, lines: tuple[str, ...], origin: str)`, an event `TypesetEvent(symbol, trigger, delay, priority, initial_value, persistent, use_values_from_trigger_time, assignments)`, an unsupported construct `TypesetUnsupported(construct, symbol)`. Text (names, notes, units) is escaped for the dialect as today.

`wrap(symbol, typeset)` is called for every symbol the printer writes, in the math and in a left hand side, including the symbols the document makes up: the rate `v_{J0}` is reported with the symbol of reaction `J0`, the amount `n_{S}` with the symbol of species `S`, the derivative `\frac{d X}{d t}` wraps the symbol of `X` inside it. Without `wrap` the output is unchanged.

`Symbol` gets the field `local: tuple[str, str] | None`, the reaction id and the original id of a local parameter, which the analysis renames to `<reaction>_<id>`, so that a caller can find the local parameter a renamed symbol stands for.

`DocumentContext` becomes a thin adapter: the templates read the `TypesetSystem` (as `system`) and the options. The golden files of typst, LaTeX and markdown stay byte identical apart from the version line, which proves the refactoring.

### Release

sbmlode 0.1.0 on PyPI.

## Part 2: sbmlutils

- `sbmlode>=0.1.0` is a dependency, the moved code, templates and tests are removed.
- The testing of the ODE export leaves sbmlutils, which makes its CI faster: the jobs `julia`, `r` and `latex` of `ci-cd.yml`, the tox envs `julia`, `r` and `latex`, `tests/converters/ode/` (with the docker and julia files), the dependencies only these tests need (the typst package, scipy for the simulator, ...) and the required checks of these jobs in `.github/rulesets/develop.json`, applied again with `apply.sh`.
- `sbmlutils.converters.ode` re-exports the public API of sbmlode (`OdeSystem`, `FORMATS`, `Format`, `render`, `write`, `render_template`), so code which uses it keeps working; its docstring and `docs/ode.md` point to sbmlode.
- Release 0.15.0. The tag 0.14.0 is pushed but 0.14.0 is not on PyPI; its release workflow is checked and fixed first.

## Part 3: sbml4humans

### Backend

A module `sbml4humans/odes.py` builds the system of a document:

```python
def ode_system(doc: libsbml.SBMLDocument, index: SIdIndex) -> tuple[OdeSystem | None, str | None]
```

It runs `sbmlode.OdeSystem.from_sbml(doc)` and `typeset("latex", "id", wrap)`. `wrap` resolves the pk of a symbol with the SId index of `links.py` of the main model (a local parameter through `Symbol.local` and the pk of its kinetic law) and returns `\htmlData{pk=<pk>}{<typeset>}`; a symbol without an element (an id a flattening of comp made up, `submodel__x`) is returned unwrapped. An exception of sbmlode is logged with its traceback and returned as the message (second element); a document without a model returns `(None, None)`.

The report model (`model.py`) gets:

```python
OdeOrigin = Literal["reactions", "rate_rule", "assignment_rule", "initial_assignment",
                    "initial_value", "concentration", "reaction", "function"]

class OdeEquation(ReportModel):
    variable: str | None   # pk of the element of the left hand side
    lhs: str               # LaTeX
    lines: list[str]       # LaTeX of the right hand side, a line after the first begins with its sign
    origin: OdeOrigin

class OdeEvent(ReportModel):
    event: str | None      # pk
    trigger: str
    delay: str | None
    priority: str | None
    initial_value: bool
    persistent: bool
    use_values_from_trigger_time: bool
    assignments: list[OdeEquation]

class OdeUnsupported(ReportModel):
    construct: str         # "AlgebraicRule", "delay", "fast reaction"
    element: str | None    # pk

class OdeSystem(ReportModel):
    odes: list[OdeEquation]
    reactions: list[OdeEquation]
    assignments: list[OdeEquation]
    functions: list[OdeEquation]
    initial: list[OdeEquation]
    events: list[OdeEvent]
    unsupported: list[OdeUnsupported]

class Report(ReportModel):
    ...
    ode_system: OdeSystem | None
    ode_error: str | None
```

The values of `OdeOrigin` are those sbmlode states; the list is completed from sbmlode while implementing and is closed (a value sbmlode adds later fails a test, not a user). `ode_error` is the message only, the traceback stays in the log, as the error contract requires.

Security: the LaTeX is printed by sbmlode from the AST, ids are SIds (sbmlode raises for another id), a pk consists of SIds, `/` and `:`, so it contains no `,`, `=` or `}` which could break out of `\htmlData`. The frontend trusts `\htmlData` and nothing else.

Size: a model with thousands of reactions adds its equations to the report, roughly the size of its kinetic laws once more. The report is compressed with gzip, which suits LaTeX well; no limit is added.

### Downloads

`GET /api/ode/examples/{example_id}`, `POST /api/ode/file`, `GET /api/ode/url?url=`, `POST /api/ode/content`, `GET /api/ode/upload/{upload_id}`, each with the query parameters `format` (one of `sbmlode.FORMATS`) and `location` (the SBML document in a COMBINE archive, as the keys of `ReportResponse.reports`). They mirror the routes of the validation, since a report is not kept on the server, and the frontend sends the source as it does for the validation. The answer is the rendered text with `Content-Disposition: attachment; filename="<model id>.<extension>"`; a failure is answered by `error_response` (status 200, `errors`), which the frontend shows as it shows a failed validation. A url and an upload are untrusted as for the report: `report_for_path(trusted=False)` rules apply, nothing next to the file is read.

### Frontend

- `report/query.ts`: `ViewState.view: "tables" | "equations"`, the query parameter `view=equations`, absent for the tables. `useReportView()` gets `setView`; a search (`q`) sets the view to the tables. The selection (`pk`) is kept when switching.
- `TypeBar.vue`: the switch "Tables | Equations" (`ViewSwitch.vue`) at its start, shown when the report of the entry has `odeSystem` or `odeError`. The type filters are hidden in the equations view, a filter which filters nothing would confuse.
- `ReportPage.vue`: `EquationsView` in the first slot of the `SplitPane` in place of `ReportTables` when `view=equations`. A narrow window shows it in place of the tables as it shows the tables.
- `components/equations/`:
  - `EquationsView.vue`: the heading with the model and `OdeDownload`, the notice of `unsupported` above all sections (amber, "the ODE system is incomplete without these constructs", each construct linked), then the sections ODE system, reaction rates, assignment rules, function definitions, initial values and events; an empty section is left out. `odeError` is shown in place of the sections with `ErrorState`. One click handler reads `data-pk` of the closest element and selects it if `ReportIndex.get(pk)` knows it; a hover over a symbol shows the name of its element as a tooltip. The symbols of the selected element are highlighted in every row, the row of the selected variable is highlighted and scrolled into view.
  - `EquationSection.vue`: the heading (glossary label, help, count), the glossary sentence, the rows.
  - `EquationRow.vue`: a grid of the left hand side, `=`, the right hand side and the origin; one line, or the lines in an `aligned` environment. Rendered with `renderLatex(..., {links: true})` when the row scrolls into view (`IntersectionObserver`), a row over `MAX_LATEX_LENGTH` gets the "render formula" button of `MathView`.
  - `EquationEvent.vue`: the event, its trigger, delay and priority, and its assignments as rows.
  - `OdeDownload.vue`: the buttons Python, Julia, R, LaTeX, Typst, Markdown.
- `report/latex.ts`: the option `links` sets `trust: (context) => context.command === "\\htmlData"` and `strict: "ignore"` for `\htmlData` only; without it nothing changes.
- `report/index.ts`: `ReportIndex.equationOf(pk)`, the equations whose `variable` is the pk.
- Inspector: `AttributesColumn.vue` shows `EquationBlock.vue` for an element with an equation, its rows and the link "show in equations" to `view=equations` with the element selected.
- Every element an end to end test uses carries a `data-testid`; no PrimeVue, no new dependency (KaTeX is there).

### Glossary and documentation

- `glossary/report.toml`: the view "Equations" and each section (ODE system, reaction rates, assignment rules, function definitions, initial values, events, unsupported constructs) with their explanation: the derivative of a state, the sum of the rates times the stoichiometry, the division by the volume of a species in concentration, the conversion factor, the order of the assignment rules. Entries for the new fields of the report model as `glossary/CLAUDE.md` requires; `uv run python -m sbml4humans.glossary` and its three outputs.
- `docs/report.md`: a section on the equations view and the downloads, the screenshot `docs/images/equations.png` taken by `scripts/screenshots.mjs`.
- `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md`: the dependency on sbmlode and the sentence on model building libraries, the module `odes.py`, the view.
- `release-notes/0.12.0.md`.

## Testing

- sbmlode: the moved tests of the export (unit, golden, numerical against the SBML test suite, the code in docker and julia), tests of `typeset` (every symbol is passed to `wrap`, made up symbols with their element, `Symbol.local`, output without `wrap` unchanged), the golden files.
- sbmlutils: one light test that `sbmlutils.converters.ode` re-exports sbmlode and renders the repressilator; nothing else of the export is tested there.
- sbml4humans backend: `odes.py` on the repressilator (6 ODEs, 12 rates, 9 rules, every symbol of a species, parameter and reaction wrapped with its pk), a model with concentrations in compartments and a conversion factor, a model with events, a comp model (a submodel symbol is unwrapped), a model with an algebraic rule (unsupported, linked), a local parameter (linked to the local parameter), a document whose analysis raises (`ode_error`, the report is complete otherwise); the download routes for every source and format, a failure in the error contract; schema, `report.ts` and fixtures regenerated.
- sbml4humans frontend: unit tests (vitest) of `query.ts` (`view`), of the `links` option of `renderLatex` (`\htmlData` renders, `\href` and `\url` do not) and of `equationOf`; an e2e test on the repressilator example: switch to the equations, the sections and their counts, a click on `v_Reaction1` opens Reaction1 in the inspector, the inspector of `X` shows its ODE and "show in equations" selects its row, a reload keeps the view, a search switches to the tables, the python download is a file with the right hand side; the e2e test of a model with an algebraic rule shows the notice.
- The rendering of every LaTeX sbmlode writes by KaTeX: a vitest test renders the equations of all fixtures with `throwOnError: true`.

## Order of work

1. sbmlode 0.1.0: extraction, typed target, release.
2. sbmlutils 0.15.0: the dependency and the re-export.
3. sbml4humans: backend, frontend, glossary, documentation, in one pull request; then release 0.12.0.

## Out of scope

Filtering the equations by the search, symbols written with names, a simulation in the browser, MathML or HTML output of sbmlode, the ODE system of a submodel definition on its own (the system is the one of the document's flattened model).
