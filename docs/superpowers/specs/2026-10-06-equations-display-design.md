# Differential equations display: design

Status: approved in conversation on 2026-10-06. Closes [#114](https://github.com/matthiaskoenig/sbml4humans/issues/114). The prototype of the user interface is `.lavish/issue-114-equations.html` (layout B chosen).

## Goal

The equations view shows the ODE system of a model in the native quantities of its state variables, in an order which reads from the definitions to the system, and shows the code sbmlode writes of it, with syntax highlighting, copy and download. The web downloads contain the ODE system only; anything else (a simulator, other symbols) is a custom export with sbmlode, which a help button links to.

## Decisions

| Question | Decision |
|---|---|
| Native quantities | In sbmlode 0.2.0, see `sbmlode/docs/design/2026-10-06-native-quantities-design.md`: a species is a state in amount or concentration as declared, `d[x]/dt = (1/V) dx/dt - ([x]/V) dV/dt` (SBML L3V2 section 3.4.6), `dV/dt` of a size with an assignment rule by the chain rule (origin `size_rate`), concentrations rescaled when an event changes a size. |
| Order of the sections | The note of the unsupported constructs, function definitions, assignment rules, reaction rates, ODE system, initial assignments, events. |
| Switch between math and code | Layout B: one row of tabs in the header of the panel, `Math` and the six formats `Python Julia R LaTeX Typst Markdown`. |
| Downloads | Code formats with `simulator=False`; documents standalone with ids as symbols. Download, copy and the link to sbmlode are in the toolbar of a code tab, for the format shown. The six buttons in the header (`OdeDownload.vue`) are removed. |
| Syntax highlighting | [Shiki](https://shiki.style) (MIT), the fine grained core with the grammars `python`, `julia`, `r`, `latex`, `typst`, `markdown` and one light theme, imported dynamically, a chunk of its own which only a code tab loads. |

## Backend

- `pyproject.toml`: `sbmlode>=0.2.0`, with the lock. Until the release the branch depends on the git revision of sbmlode, the dependency is switched to the release before the merge.
- `model.OdeOrigin`: `concentration` removed, `size_rate` added; the schema (`python -m sbml4humans.schema`), `report.ts` and the fixtures are regenerated.
- `odes._Links`: the symbol of a size rate links to its compartment (its source is the compartment); the event and assignment equations are unchanged in shape.
- `report.ode_for_path(path, fmt, location, trusted, simulator=False)`: the code formats are rendered with `simulator`, the documents with their defaults (`standalone`, `symbols="id"`). The endpoints `/api/ode/...` keep their routes and pass no option, so the web gets the ODE system only; a python caller may pass `simulator=True`.
- Glossary: `odeInitial` is labelled "initial assignments" and its text describes the conversions of 0.2.0 (no amount the system integrates); the origin `size_rate` and the text of `equations` (the order of the sections), `odeSystem` (native quantities, the term of the dilution) and `odeDownload` (the ODE system only, the custom exports of sbmlode with a link to <https://matthiaskoenig.github.io/sbmlode/formats/>) are updated; `python -m sbml4humans.glossary` regenerates the outputs.

## Frontend

### State

`ReportViewState` gets `code: OdeFormat | null`, kept in the query as `?view=equations&code=python` (`report/query.ts`); `null` is the math, the default of the view. Every tab names its format, so nothing else is remembered.

The store caches the code per `(location, format)` of the current report: `odeCode(format, location): Promise<OdeDownloadFile>` calls the download of the source once and returns the cached file afterwards; the cache is cleared with the report. A failed request is not cached.

### Components

- `EquationsView.vue`: the header holds the label, help, the model link and `EquationTabs`; below it either the math (as today, the sections in the new order) or `EquationCode`. The sections table `SECTIONS` becomes `functions, assignments, reactions, odes, initial`, events after them; the unsupported note stays first.
- `EquationTabs.vue` (new): a `role="tablist"` row, `Math`, a separator, the six formats; arrow keys move between the tabs; each tab has a `data-testid` (`equations-tab-math`, `equations-tab-python`, ...). It wraps below the model link in a narrow panel.
- `EquationCode.vue` (new): a toolbar with the file name, Copy (the clipboard, "Copied" for a moment), Download (the cached text as a file, no second request) and a `HelpButton` with the text of `odeDownload` and the link "custom exports with sbmlode"; below it the highlighted code in a scrolling `pre`, lines not wrapped. While the code loads, a loading state; a failure shows in `ErrorState`, e.g. code of a model with an unsupported construct.
- `report/highlight.ts` (new): `highlight(code, format): Promise<string>`, which imports Shiki on its first call and keeps the highlighter; the HTML of Shiki is set with `v-html`, it escapes the code.
- `OdeDownload.vue` is removed with its e2e test.

### Tests

- Backend: `size_rate` in the report of a model with a compartment of an assignment rule (an example of the test suite added to `tests/data`), the native concentration ODE of a model with a compartment of a rate rule, `ode_for_path` without and with `simulator`.
- Frontend unit: the query of `code`, the order of the sections, the cache of the store.
- e2e: the tabs switch between math and code and keep the format in the url, a reload shows the same tab, copy and download of a code tab, the error of a format which fails, a model with a compartment of a rate rule shows `dS/dt` with the term of the dilution.
- The screenshot `docs/images/report-equations.png` is retaken and one of a code tab is added to `docs/report.md`.

## Order of the work

1. sbmlode: native quantities, size rates, the differentiator, release 0.2.0.
2. sbml4humans: this design, against the git revision of sbmlode, switched to 0.2.0 before the merge.
