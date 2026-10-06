# Differential equations (issue #5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the complete ODE system of a model in sbml4humans, typeset by a new package `sbmlode` extracted from sbmlutils, with every symbol linked to its element and downloads of the system as code and documents.

**Architecture:** `sbmlode` (new repository, extracted from `sbmlutils.converters.ode`) gets a typed target `OdeSystem.typeset(dialect, symbols, wrap)` returning frozen dataclasses; `wrap` transforms the `sid -> symbol` mapping the printers already take. sbmlutils depends on and re-exports sbmlode. sbml4humans maps the typeset system into its report model (`Report.ode_system`), symbols wrapped as `\htmlData{pk=...}`, and renders it in a new "Equations" view with KaTeX.

**Tech Stack:** python-libsbml, jinja2, pydantic, FastAPI, Vue 3, KaTeX, vitest, playwright, zensical, uv, ruff, ty.

**Spec:** `specs/2026-10-06-differential-equations-design.md`

## Global Constraints

- sbmlode depends on python-libsbml and jinja2 only; python 3.11 to 3.15.
- sbml4humans adds no SBML model building library; sbmlode reads and prints only.
- Symbols are typeset from ids, never names.
- The frontend never builds a pk; pks come from the backend (`ModelIndex.resolve`).
- KaTeX trusts `\htmlData` and nothing else, only when `links: true`.
- Every failure of the api answers status 200 with `{"errors": [...]}` (error contract); `ode_error` carries the message only.
- Never use the em dash; markdown has no hard line wraps; no agent attribution anywhere.
- Golden files of sbmlode stay byte identical apart from the "written by" version line.
- Every element an e2e test uses has a `data-testid`; every name and explanation comes from `glossary/*.toml`.

## Review Focus

- A document with no model, or only model definitions: no switch, no error (`ode_system=None, ode_error=None`).
- A model sbmlode refuses (invalid, unsupported level) or that raises inside sbmlode: the report is complete, the view shows the error.
- A reaction without kinetic law, a model of fbc only (no kinetic laws): the system renders with zero rates as sbmlode states, no crash.
- A symbol whose id has no element in the report (flattened comp ids, renamed locals): rendered unwrapped, a click does nothing.
- A model with thousands of reactions: rows render lazily, the page stays responsive; a row over `MAX_LATEX_LENGTH` gets the "render formula" button.

---

## Part 1: sbmlode (repository `/home/mkoenig/git/sbmlode`)

### Task 1: Package extracted and decoupled from sbmlutils

**Files:**
- Create: `src/sbmlode/` (from `sbmlutils/src/sbmlutils/converters/ode/`), `src/sbmlode/templates/` (from `sbmlutils/src/sbmlutils/resources/converters/ode/`), `src/sbmlode/io.py`, `src/sbmlode/units.py`, `tests/` (from `sbmlutils/tests/converters/ode/`), `tests/data/` (models the tests use)
- Modify: every moved module importing `sbmlutils`

**Interfaces:**
- Produces: `sbmlode.OdeSystem`, `FORMATS`, `Format`, `render`, `write`, `render_template`, `__version__ = "0.1.0"`; `sbmlode.io.read_document(source) -> libsbml.SBMLDocument`, `sbmlode.io.flatten(doc) -> libsbml.SBMLDocument`, `sbmlode.units.udef_to_string(udef, model) -> str | None`.

- [ ] Copy the files, rename imports `sbmlutils.converters.ode` to `sbmlode`, `RESOURCES_DIR / "converters" / "ode"` to `Path(__file__).parent / "templates"`.
- [ ] Port `read_sbml` (the subset used: path, string, document; errors as `ValueError`), `flatten_sbml_doc` (libsbml `CompFlatteningConverter`, options as sbmlutils sets them) and `udef_to_string` with their tests from sbmlutils into `io.py` / `units.py`.
- [ ] Copy test models into `tests/data/`; the SBML test suite test downloads the suite (cached under `platformdirs.user_cache_dir("sbmlode")`, a test dependency) and skips offline.
- [ ] `sbmlutils.__version__` in templates/context becomes `sbmlode.__version__`, key `sbmlode`; regenerate golden files and check with `git diff --word-diff` that only that line changed.
- [ ] Run `uv run pytest -q -x`; all pass. Commit "sbmlode extracted from sbmlutils e20bd0aa (#492)".

### Task 2: Project setup

**Files:** `pyproject.toml`, `uv.lock`, `tox.ini`, `lowest-overrides.txt`, `LICENSE`, `README.md`, `CITATION.cff`, `.zenodo.json`, `.gitignore`, `.github/workflows/{ci-cd,ruff,ty,docs}.yml`, `.github/rulesets/{develop,main,tags,tag-creation}.json`, `.github/rulesets/apply.sh`, `CLAUDE.md`, `release-notes/0.1.0.md`, `src/sbmlode/releasenotes.py`, `zensical.toml`, `docs/*.md`

- [ ] Adapt from sbmlutils: `pyproject.toml` (hatchling, deps, optional `test` group: pytest, typst, scipy, platformdirs; dev: ruff, ty, tox-uv, bump-my-version, zensical), ruff and ty config, bump-my-version (files: `pyproject.toml`, `src/sbmlode/__init__.py`, `CITATION.cff`; `tag = false`; hook regenerating release notes).
- [ ] `tox.ini`: py3.11..3.15, lowest, ty, julia, r, latex envs (moved from sbmlutils, paths adapted).
- [ ] Workflows from sbmlutils: `ci-cd.yml` jobs test/tests/julia/r/latex/build/publish/github-release/sync-main (cobra dropped); `ruff.yml`, `ty.yml`; `docs.yml` from sbml4humans (release notes check, strict build, deploy from develop).
- [ ] `releasenotes.py` from sbml4humans adapted; `docs/`: index, formats, typeset (typed target and wrap), api, design (the moved spec), development (commands, releases), release-notes (generated); `zensical.toml` from sbmlutils adapted.
- [ ] Rulesets from sbmlutils, required checks `tests`, `julia`, `r`, `latex`, `ruff`, `ty`, `docs`.
- [ ] `uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run python -m sbmlode.releasenotes --check && uv run zensical build --clean --strict`; all clean. Commit.

### Task 3: Typed target with `wrap`

**Files:**
- Modify: `src/sbmlode/system.py` (`Symbol.element`), `src/sbmlode/analysis.py` (set it), `src/sbmlode/documents.py` (dataclasses, `typeset`), `src/sbmlode/__init__.py`
- Test: `tests/test_ode_typeset.py`

**Interfaces:**
- Produces:
  - `Symbol.element: tuple[str, ...]` — `(sid,)` for an element of the model, `(reaction_id, local_id)` for a renamed local parameter, `(species_id,)` for the amount of a species held as amount.
  - `OdeSystem.typeset(dialect: Literal["latex","typst"]="latex", symbols: Literal["id","name"]="id", wrap: Callable[[Symbol, str], str] | None = None) -> TypesetSystem`
  - `TypesetEquation(variable: Symbol | None, lhs: str, lines: tuple[str, ...], origin: str)`, `TypesetEvent(symbol: Symbol, trigger: str, delay: str|None, priority: str|None, initial_value: bool, persistent: bool, use_values_from_trigger_time: bool, assignments: tuple[TypesetEquation, ...])`, `TypesetUnsupported(construct: str, element: str)`, `TypesetSystem(model, units, compartments, species, parameters, functions, initial, assignments, amounts, reactions, odes, events, unsupported)`.

- [ ] Write the failing tests:

```python
def test_wrap_sees_every_symbol(repressilator: OdeSystem) -> None:
    seen: list[tuple[str, ...]] = []
    def wrap(symbol: Symbol, typeset: str) -> str:
        seen.append(symbol.element)
        return rf"\htmlData{{id={symbol.element[-1]}}}{{{typeset}}}"
    t = repressilator.typeset("latex", "id", wrap)
    assert len(t.odes) == 6 and len(t.reactions) == 12
    assert r"\htmlData{id=PX}" in t.odes[0].lhs
    assert r"\htmlData{id=Reaction4}" in t.odes[0].lines[0]
    assert ("Reaction1",) in seen

def test_without_wrap_unchanged(repressilator: OdeSystem) -> None:
    assert repressilator.render("latex") == REPRESSILATOR_GOLDEN_TEX

def test_local_parameter_element(local_model: OdeSystem) -> None:
    sym = local_model.symbol("J0_k1")
    assert sym.element == ("J0", "k1")

def test_amount_element(amount_model: OdeSystem) -> None:
    amounts = amount_model.amounts
    assert amounts[0].symbol.element == (str(amounts[0].amount_of),)
```

- [ ] Run `uv run pytest tests/test_ode_typeset.py -q`; FAIL.
- [ ] Implement: `Symbol.element` with default `()` meaning `(sid,)` via a property `Symbol.source` returning `self.element or (self.sid,)`; set in `analysis` for locals and amounts. In `DocumentContext.__init__(system, fmt, symbols, wrap=None)` apply after `_symbols`: `self.symbols = {sid: wrap(system.symbol(sid), t) for sid, t in self.symbols.items()}` when `wrap`. Convert the dicts of `build` into the dataclasses (attribute names = old keys; Jinja attribute lookup keeps the templates unchanged). `OdeSystem.typeset` = `DocumentContext(self, dialect, symbols, wrap).typeset()`.
- [ ] Run the full suite; golden files unchanged. ruff, ty clean. Commit.

### Task 4: Publish sbmlode 0.1.0

- [ ] Push `develop` (initial setup goes directly before the rulesets are applied), set `develop` default branch, apply rulesets (`.github/rulesets/apply.sh`), enable Pages for `develop` in the `github-pages` environment.
- [ ] Check CI green on develop; confirm with the user, then tag `0.1.0` on develop and push; the release workflow publishes to PyPI. Verify `pip index versions sbmlode`.

## Part 2: sbmlutils (repository `/home/mkoenig/git/sbmlutils`)

### Task 5: sbmlutils on sbmlode, ODE testing removed

**Files:** `pyproject.toml`, `uv.lock`, `src/sbmlutils/converters/ode/__init__.py` (re-export only), remove the other modules of `converters/ode/`, `src/sbmlutils/resources/converters/ode/`, `tests/converters/ode/`; `tox.ini` (julia, r, latex envs), `.github/workflows/ci-cd.yml` (julia, r, latex jobs), `.github/rulesets/develop.json` (their checks), `docs/ode.md`, `docs/api/converters.ode.md`, `examples/converters/ode.py`, `release-notes/0.15.0.md`
- Test: `tests/converters/test_ode_reexport.py`

- [ ] First check why 0.14.0 is not on PyPI (`gh-axi run list`), fix it.
- [ ] Failing test:

```python
def test_reexport() -> None:
    import sbmlode
    from sbmlutils.converters import ode
    assert ode.OdeSystem is sbmlode.OdeSystem
    system = ode.OdeSystem.from_sbml(REPRESSILATOR_SBML)
    assert "dX" in system.render("markdown") or r"\frac{\mathrm{d} X}" in system.render("markdown")
```

- [ ] Replace, remove, adapt docs to point to sbmlode; `uv run pytest -q -x`, ruff, ty, docs build green. Branch, PR, merge; apply rulesets; release 0.15.0 (release notes, bump, PR, tag) after confirming with the user.

## Part 3: sbml4humans (branch `issue-5-differential-equations`)

### Task 6: Backend report of the ODE system

**Files:**
- Create: `backend/sbml4humans/odes.py`, `backend/tests/test_odes.py`
- Modify: `backend/pyproject.toml` (+ `sbmlode>=0.1.0`), `uv.lock`, `backend/sbml4humans/model.py` (Ode models, `Report.ode_system`, `Report.ode_error`), `backend/sbml4humans/sbmlinfo.py` (`build_report`), `glossary/report.toml` (+ fields), schema, `frontend/src/types/report.ts`, `frontend/tests/fixtures/*.json`, glossary outputs

**Interfaces:**
- Produces: `odes.ode_system(doc: libsbml.SBMLDocument, model: Model) -> tuple[OdeSystem | None, str | None]` (report `OdeSystem` pydantic model); json (camelCase by alias) `odeSystem{odes, reactions, assignments, functions, initial: OdeEquation[], events: OdeEvent[], unsupported: OdeUnsupported[]}`, `odeError`.

- [ ] Failing tests (repressilator example, a local-parameter model, algebraic rule, comp, raising analysis via monkeypatch, no model):

```python
def test_repressilator_system() -> None:
    report = report_of(EXAMPLE_REPRESSILATOR)
    ode = report.ode_system
    assert ode is not None and report.ode_error is None
    assert (len(ode.odes), len(ode.reactions), len(ode.assignments)) == (6, 12, 9)
    assert ode.odes[0].variable == "BIOMD0000000012/Species:PX"  # pk format of sbmlinfo
    assert r"\htmlData{pk=BIOMD0000000012/Reaction:Reaction4}" in ode.odes[0].lines[0]

def test_analysis_error_is_contained(monkeypatch) -> None:
    monkeypatch.setattr(sbmlode.OdeSystem, "from_sbml", boom)
    report = report_of(EXAMPLE_REPRESSILATOR)
    assert report.ode_system is None and report.ode_error == "boom"
    assert report.models  # rest intact

def test_unresolved_symbol_unwrapped() -> None: ...   # comp model: a flattened id has no \htmlData
def test_local_parameter_linked() -> None: ...         # pk of the LocalParameter of the kinetic law
def test_algebraic_rule_unsupported() -> None: ...     # unsupported[0].construct, element pk
def test_no_model() -> None: ...                       # (None, None)
```

- [ ] Implement `odes.py`:

```python
def ode_system(doc: libsbml.SBMLDocument, model: Model) -> tuple[OdeSystem | None, str | None]:
    """The ODE system of the model of a document, or the message of its failure."""
    index = ModelIndex(model)
    def pk_of(symbol: sbmlode.Symbol) -> str | None:
        element = symbol.source
        if len(element) == 2:
            reaction = index.resolve(element[0])
            law = f"{reaction}/kineticLaw" ...  # resolve through model.list_of_reactions -> kinetic_law.pk
            return index.resolve(element[1], law_pk)
        return index.resolve(element[0])
    def wrap(symbol: sbmlode.Symbol, typeset: str) -> str:
        pk = pk_of(symbol)
        return typeset if pk is None else rf"\htmlData{{pk={pk}}}{{{typeset}}}"
    try:
        typeset = sbmlode.OdeSystem.from_sbml(doc).typeset("latex", "id", wrap)
    except Exception as err:
        logger.exception("The ODE system of the model could not be built.")
        return None, str(err) or type(err).__name__
    return _convert(typeset, pk_of), None
```

  `_convert` maps `TypesetEquation` to `OdeEquation(variable=pk_of(eq.variable) if eq.variable else None, lhs, lines=list(lines), origin)`, events and unsupported likewise (unsupported element: `index.resolve(id)` or meta id). Call in `build_report` for the `kind="model"` model only.
- [ ] Glossary entries for the new fields, `uv run python -m sbml4humans.glossary`, `python -m sbml4humans.schema`, `npm run types`, `npm run fixtures`.
- [ ] `uv run pytest -q -x`, ruff, ty clean. Commit.

### Task 7: Download routes

**Files:** `backend/sbml4humans/api.py`, `backend/sbml4humans/odes.py` (`render_ode(content: bytes, location: str | None, fmt: str) -> tuple[str, str]` filename, text), `backend/tests/test_api_ode.py`

- [ ] Failing tests: every route (`/api/ode/examples/{id}`, `/api/ode/file`, `/api/ode/url`, `/api/ode/content`, `/api/ode/upload/{id}`) with `format=python` answers 200 with `content-disposition: attachment; filename="BIOMD0000000012.py"` and `def ` in the body; an unknown format, an unknown location and a model sbmlode refuses answer 200 with `errors`.
- [ ] Implement with the reading of documents `report.py` uses for bytes and archives (by location, the master or the only SBML file when absent), `error_response` on failure; routes under the tag `ode`.
- [ ] Tests, ruff, ty. Commit.

### Task 8: Frontend view state, switch and KaTeX links

**Files:** `frontend/src/report/query.ts`, `frontend/src/report/view.ts`, `frontend/src/report/latex.ts`, `frontend/src/report/index.ts` (`equationOf`), `frontend/src/components/report/ViewSwitch.vue`, `TypeBar.vue`, `pages/ReportPage.vue`, unit tests

- [ ] Failing vitest tests: `parseQuery({view: "equations"}).view === "equations"`, absent → `"tables"`, `toQuery` omits tables; setting `q` resets view; `renderLatex("\\htmlData{pk=a/b:c}{x}", {links: true})` contains `data-pk="a/b:c"`, without links it does not; `\href{javascript:...}` never renders a link; `equationOf(pk)`.
- [ ] Implement; `ViewSwitch` (`data-testid="view-switch"`, buttons `view-tables`, `view-equations`) at the start of TypeBar when `odeSystem || odeError`; type filters hidden in the equations view; labels from the glossary.
- [ ] `npm run test:unit`, `npm run lint`, `npm run build`. Commit.

### Task 9: Equations view and inspector block

**Files:** `frontend/src/components/equations/{EquationsView,EquationSection,EquationRow,EquationEvent,OdeDownload,EquationBlock}.vue`, `frontend/src/components/inspector/AttributesColumn.vue`, `frontend/src/report/odeDownload.ts`, `glossary/report.toml` (view and section entries), glossary outputs, fixture KaTeX test

- [ ] Vitest: render every equation of every fixture with KaTeX `throwOnError: true` and `links: true`.
- [ ] Implement as specified in the spec (sections order: unsupported notice, ODE system, reaction rates, assignment rules, function definitions, initial values, events; lazy rows by IntersectionObserver; click delegation; highlight; name tooltip; download through the same source handling as the validation request; `EquationBlock` in the inspector with "show in equations").
- [ ] `npm run test:unit`, lint, build; check in the browser (`npm run dev` + backend) against the lavish prototype. Commit.

### Task 10: E2E, documentation, release notes

**Files:** `frontend/tests/e2e/equations.spec.ts`, `docs/report.md`, `docs/images/equations.png`, `frontend/scripts/screenshots.mjs`, `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `release-notes/0.12.0.md`

- [ ] E2E on the repressilator example as in the spec's Testing section, plus the algebraic rule notice.
- [ ] Docs, screenshot, CLAUDE.md sentences, release notes. All checks: pytest, ruff, ty, glossary --check, releasenotes --check, zensical strict, unit, e2e, build.
- [ ] PR against develop; CI green.
