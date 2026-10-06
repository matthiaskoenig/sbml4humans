# Differential equations display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The equations view shows the ODE system in the native quantities of the SBML state variables, in the order definitions to system, and shows the code of the six sbmlode formats in tabs with highlighting, copy and download (issue #114).

**Architecture:** The math changes in sbmlode (0.2.0): the amount `n_S` disappears, a concentration ODE gets the dilution term `-(S/V) dV/dt`, `dV/dt` is an assignment of origin `size_rate` (the rate rule of `V`, or the chain rule of its assignment rule by a differentiator of sbmlode), and an event which changes a size rescales the concentrations with the size after the event (a `sizes` function in the code). sbml4humans takes the new typeset system unchanged in shape, renders the code without the simulator, and the frontend gets a tab row `Math | Python Julia R LaTeX Typst Markdown` with a code tab highlighted by Shiki.

**Tech Stack:** python 3.14, libsbml 5.21, jinja2, pytest, roadrunner (reference); FastAPI, pydantic; Vue 3, TypeScript ~6.0.3, Vitest, Playwright, Shiki.

**Spec:** `sbmlode/docs/design/2026-10-06-native-quantities-design.md` and `sbml4humans/docs/superpowers/specs/2026-10-06-equations-display-design.md`.

## Global Constraints

- sbmlode repository `~/git/sbmlode`, branch `native-quantities` from `origin/develop`; sbml4humans repository `~/git/sbml4humans`, branch `equations-display-114`.
- sbmlode version 0.2.0, a breaking change of the system: `OdeSystem.amounts`, `Quantity.amount_of`, `Ode.amount_of`, the origin `concentration` and `divisor_position` of the code context are removed.
- Concentration ODE: `d[x]/dt = (1/V) dx/dt - ([x]/V) dV/dt` (SBML L3V2 Release 2, section 3.4.6).
- Every semantic case of the SBML test suite 3.4.0 which passes with sbmlode 0.1.0 in python passes with 0.2.0 (baseline in `scratchpad/report_before.txt`), julia and R as far as they run locally.
- No dependency on an SBML model building library in sbml4humans; new frontend dependencies MIT/ISC or comparable (Shiki: MIT).
- No em dash; markdown without hard wraps; no attribution lines in commits or PRs; CHANGELOG and generated files are never edited by hand.
- Backend: ruff, `ty check` with zero diagnostics, google docstrings on every module, class, function.
- Every element an e2e test uses carries a `data-testid`.

## Review Focus

1. A concentration in a compartment with an assignment rule of time and states (`V = V0 + k*S1`): the chain rule must match roadrunner numerically; pinned by the test suite sweep (cases with assigned compartments) and `test_size_rate_of_assigned_compartment_matches_roadrunner` (Task 3).
2. An event which assigns a parameter of the assignment rule of a size: the concentrations jump with `V_before / V_after`; pinned by `test_event_resizes_assigned_compartment` (Task 4).
3. A rule of a size which cannot be differentiated (`delay` in it): the unsupported construct `rate of an assigned size`, code refuses to render, the typeset system still renders; pinned by `test_size_rate_not_differentiable` (Task 3) and the report test (Task 7).
4. The code tab of a large model (thousands of lines): highlighting must not block the page; the code above `HIGHLIGHT_LIMIT` (200 000 characters) is shown plain; pinned by a unit test of `highlight` (Task 9).
5. A url with `?code=` of an unknown format, a change of the archive entry with a code tab open: an unknown format is the math, the code is per location; pinned by `query.test.ts` and `reportStore.test.ts` (Task 9).

---

## Part 1: sbmlode 0.2.0

### Task 1: the differentiator `astutil.derivative`

**Files:**
- Modify: `src/sbmlode/astutil.py`
- Test: `tests/test_ode_astutil.py`

**Interfaces:**
- Produces: `TIME: str` (the variable name for the csymbol time, `"\x00time"`), `derivative(ast: libsbml.ASTNode, variable: str) -> libsbml.ASTNode | None`, a new math, simplified (no `0 *`, `1 *`, `+ 0`, `^ 1`); `None` for a node it does not know (delay, rateOf, a call of a function definition, distrib, csymbols of packages, `factorial`, `ceiling`/`floor` return `0` because their derivative is 0 almost everywhere).

- [ ] **Step 1: Write the failing tests**

```python
import math
import random

import libsbml
import pytest

from sbmlode.astutil import TIME, derivative


def _value(ast: libsbml.ASTNode, values: dict[str, float]) -> float:
    """Evaluate a math with python, the names bound to the values."""
    formula = libsbml.formulaToL3String(ast)
    env = {"exp": math.exp, "ln": math.log, "log10": math.log10, "sqrt": math.sqrt,
           "sin": math.sin, "cos": math.cos, "tan": math.tan, "abs": abs,
           "pow": math.pow, "arctan": math.atan, "sinh": math.sinh, "cosh": math.cosh}
    return eval(formula.replace("^", "**"), env, dict(values))  # noqa: S307


EXPRESSIONS = [
    "x", "2 * x", "x * y", "x / y", "x^3", "x^y", "y^x", "exp(k * x)", "ln(x)",
    "sqrt(x)", "sin(x) * cos(x)", "tan(x)", "arctan(x)", "sinh(x) + cosh(x)",
    "V0 * (1 + k * x)", "x^2 / (K + x^2)", "-x", "pow(x, 2.5)", "abs(x - 3)",
]


@pytest.mark.parametrize("formula", EXPRESSIONS)
def test_derivative_matches_finite_difference(formula: str) -> None:
    ast = libsbml.parseL3Formula(formula)
    d = derivative(ast, "x")
    assert d is not None
    rng = random.Random(formula)
    for _ in range(5):
        values = {n: rng.uniform(0.5, 2.0) for n in ("x", "y", "k", "K", "V0")}
        h = 1e-6
        up, down = dict(values, x=values["x"] + h), dict(values, x=values["x"] - h)
        expected = (_value(ast, up) - _value(ast, down)) / (2 * h)
        assert _value(d, values) == pytest.approx(expected, rel=1e-5, abs=1e-8)


def test_derivative_of_other_name_is_zero() -> None:
    assert libsbml.formulaToL3String(derivative(libsbml.parseL3Formula("y + 2"), "x")) == "0"


def test_derivative_simplifies() -> None:
    d = derivative(libsbml.parseL3Formula("k * x"), "x")
    assert libsbml.formulaToL3String(d) == "k"


def test_derivative_of_time() -> None:
    ast = libsbml.parseL3Formula("V0 * exp(k * time)")  # L3 parser: time is the csymbol
    d = derivative(ast, TIME)
    assert libsbml.formulaToL3String(d) == "V0 * (k * exp(k * time))"


def test_derivative_of_piecewise_keeps_conditions() -> None:
    d = derivative(libsbml.parseL3Formula("piecewise(2 * x, x > 1, x^2)"), "x")
    assert libsbml.formulaToL3String(d) == "piecewise(2, x > 1, 2 * x)"


@pytest.mark.parametrize("formula", ["delay(x, 1)", "f(x)", "rateOf(x)"])
def test_derivative_unsupported(formula: str) -> None:
    assert derivative(libsbml.parseL3Formula(formula), "x") is None
```

- [ ] **Step 2: Run the tests**: `uv run pytest tests/test_ode_astutil.py -q -x`; expected: ImportError of `derivative`.
- [ ] **Step 3: Implement** `derivative` in `astutil.py`: a recursive function over the node types, built with the helpers `node`, `number`, `name`, `product`, `signed_sum`, and local simplifying constructors `_add(a, b)`, `_mul(a, b)`, `_div(a, b)` which drop `0` and `1` (a number node whose value is 0 or 1). Rules: `AST_PLUS` sum of the derivatives; `AST_MINUS` unary and binary; `AST_TIMES` n-ary product rule `Σ_i u_i' Π_{j≠i} u_j`; `AST_DIVIDE` `(u'v - uv')/v^2`; `AST_POWER`/`AST_FUNCTION_POWER` `n u^(n-1) u'` for a number exponent, else `u^v (v' ln(u) + v u'/u)`; `AST_FUNCTION_EXP` `exp(u) u'`; `AST_FUNCTION_LN` `u'/u`; `AST_FUNCTION_LOG` with base `b` (the first child, 10 if one child) `u'/(u ln(b))`; `AST_FUNCTION_ROOT` as power `u^(1/n)`; `AST_FUNCTION_ABS` `piecewise(u', u > 0, -u')`; the trigonometric and hyperbolic functions and their inverses by their table; `AST_FUNCTION_PIECEWISE` each value differentiated, the conditions copied; `AST_FUNCTION_CEILING`/`FLOOR` and every relational or logical node: `0`; numbers, `AST_CONSTANT_*`, `AST_NAME_AVOGADRO`: `0`; `AST_NAME` `1` if its name is the variable else `0`; `AST_NAME_TIME` `1` if the variable is `TIME`; every other type (`AST_FUNCTION`, delay, rateOf, distrib, `AST_CSYMBOL_FUNCTION`): `None`, and `None` of a child propagates.
- [ ] **Step 4: Run the tests**: `uv run pytest tests/test_ode_astutil.py -q`; expected: PASS. Adjust the expected strings of `test_derivative_of_time` and `test_derivative_of_piecewise_keeps_conditions` only to an equivalent simplified form, the finite difference test is the arbiter.
- [ ] **Step 5: Lint and commit**: `uv run ruff check . && uv run ruff format --check . && uv run ty check`; `git commit -am "astutil.derivative: the symbolic derivative of a math"`.

### Task 2: the system without amounts, with size rates

**Files:**
- Modify: `src/sbmlode/system.py`
- Test: `tests/test_ode_system.py`

**Interfaces:**
- Produces:
  - `Kind` gains `"rate"`; `Origin` loses `"concentration"`, gains `"size_rate"`; `Ode.origin: Literal["reactions", "rate_rule", "dilution"]`.
  - `Quantity` without `amount_of`; `Ode` without `amount_of`, with `size_rate: str | None = None` (the id of the rate of the compartment in the dilution term).
  - `@dataclass(frozen=True, eq=False) class SizeRate: symbol: Symbol; compartment: str; math: libsbml.ASTNode | None` (the math is `None` if it cannot be differentiated).
  - `OdeSystem.size_rates: tuple[SizeRate, ...]` replaces `amounts`; `OdeSystem.quantities` is compartments, species, parameters, species references; `_symbols` includes `r.symbol` of every size rate.
  - `EventAssignment.divisor: str | None`: the compartment whose size after the assignments of the event divides the value, a compartment the event assigns or a compartment with an assignment rule.

- [ ] **Step 1**: change the dataclasses and the module docstring (the bullets "Species", "A species in concentration in a variable compartment", "`rateOf(x)`", "Unsupported" of the docstring describe native quantities, size rates, dilution and the rescaling, as in the spec).
- [ ] **Step 2**: `uv run ty check` lists every user of `amounts`/`amount_of`; these are fixed in Tasks 3 to 5, the commit is made with Task 3.

### Task 3: the analysis of native quantities and size rates

**Files:**
- Modify: `src/sbmlode/analysis.py`
- Test: `tests/test_ode_system.py`, `tests/data/models/` (new `variable_compartment.xml`, also copied to sbml4humans in Task 7)

**Interfaces:**
- Consumes: `derivative`, `TIME` (Task 1), `SizeRate`, `Ode.size_rate` (Task 2).
- Produces: `analyse(...)` returns the system of the spec; `_Analysis._size_rate(cid: str) -> str | None` the id of the rate of a compartment whose size changes continuously (created once, `None` for a constant size or one changed by events only); `_Analysis._total_rate(sid: str, element: str, stack: frozenset[str]) -> libsbml.ASTNode | None`.

The model `variable_compartment.xml` (L3V2, written by hand): compartments `Vc` (size 1, rate rule `k_g * Vc`), `Va` (assignment rule `Va0 * (1 + k_a * time) + 0.1 * S1`), `Ve` (size 1, changed by the event `grow` at `time > 2` to 2); species in concentration `S1` in `Vc` (initialConcentration 1), `S2` in `Va` (initialAmount 1), `S3` in `Ve` (initialConcentration 1), boundary `B` in `Vc` (initialConcentration 1); reactions `J1: S1 -> S2` (`k1 * S1 * Vc`), `J2: S2 -> S3` (`k2 * S2 * Va`); parameters `k_g = 0.1`, `k_a = 0.2`, `Va0 = 1`, `k1 = 1`, `k2 = 0.5`.

- [ ] **Step 1: Write the failing tests** in `tests/test_ode_system.py`:

```python
def test_concentration_in_rate_rule_compartment_is_native() -> None:
    system = OdeSystem.from_sbml(MODELS / "variable_compartment.xml")
    assert "S1" in system.states and not any(s.startswith("n_") for s in system.states)
    ode = next(o for o in system.odes if o.variable == "S1")
    rate = ode.size_rate
    assert rate is not None and system.symbol(rate).source == ("Vc",)
    assert libsbml.formulaToL3String(ode.rhs) == f"-J1 / Vc - S1 / Vc * {rate}"
    size_rate = next(a for a in system.assignments if a.variable == rate)
    assert size_rate.origin == "size_rate"
    assert libsbml.formulaToL3String(size_rate.math) == "k_g * Vc"


def test_size_rate_of_assigned_compartment_is_the_chain_rule() -> None:
    system = OdeSystem.from_sbml(MODELS / "variable_compartment.xml")
    rate = next(r for r in system.size_rates if r.compartment == "Va")
    # dVa/dt = Va0 * k_a + 0.1 * dS1/dt, dS1/dt inlined
    formula = libsbml.formulaToL3String(rate.math)
    assert formula.startswith("Va0 * k_a + 0.1 * ")


def test_boundary_concentration_in_growing_compartment_is_diluted() -> None:
    system = OdeSystem.from_sbml(MODELS / "variable_compartment.xml")
    ode = next(o for o in system.odes if o.variable == "B")
    assert ode.origin == "dilution"


def test_event_resizing_rescales_concentrations() -> None:
    system = OdeSystem.from_sbml(MODELS / "variable_compartment.xml")
    (event,) = system.events
    rescaled = [a for a in event.assignments if a.variable == "S3"]
    assert rescaled and rescaled[0].divisor == "Ve" and rescaled[0].math is None


def test_size_rate_not_differentiable() -> None:
    sbml = (MODELS / "variable_compartment.xml").read_text().replace(
        "<ci> k_a </ci>", "<apply><csymbol encoding=\"text\" definitionURL=\"http://www.sbml.org/sbml/symbols/delay\"> delay </csymbol><ci> k_a </ci><cn> 1 </cn></apply>", 1
    )
    system = OdeSystem.from_sbml(sbml)
    assert ("rate of an assigned size", "Va") in system.unsupported
    with pytest.raises(ValueError, match="rate of an assigned size"):
        system.render("python")
    system.typeset()  # the documents still render
```

  and `test_size_rate_of_assigned_compartment_matches_roadrunner` in `tests/test_ode_python.py`, which renders the python code of `variable_compartment.xml`, simulates it to t=5 and compares `S1, S2, S3, B` with roadrunner (`[S1]` ...), using the helpers of `test_ode_python.py` that the curated cases use (`python_module`, `assert_trajectory_as_roadrunner`).

- [ ] **Step 2**: `uv run pytest tests/test_ode_system.py -q -x -k "native or chain or dilut or rescal or differentiable"`; expected: FAIL.
- [ ] **Step 3: Implement** in `analysis.py`:
  - remove `self.amounts`, `_with_amounts`, `_concentration` and the amount branch of `_read_species`; a species keeps `role` as before, except: a species in concentration (`not in_amount`) without a rule of its own, in a compartment whose size changes continuously (`self._role(cid) != "constant"`) and whose role is not `state`, becomes a `state` (its ODE is the dilution); record these in `self.diluted: set[str]`.
  - `_size_rate(cid)`: if `cid` has neither a rate nor an assignment rule, `None`; else create once `rid = self._unique(f"d{cid}_dt")`, the symbol `Symbol(rid, f"rate of {name or cid}", f"{unit}/{time unit}" if both else None, None, "rate", (cid,))`, store `self.size_rates[cid] = (symbol, math)` where math is filled in `system()` after the odes are built: `self._resolved_rate(cid, cid)` for a rate rule, `self._total_rate(cid, cid, frozenset())` for an assignment rule; `None` math adds `("rate of an assigned size", cid)` to unsupported.
  - `_build_odes`: for a species in concentration with reactions: `rhs = (terms / V) - (S / V) * rate` if `_size_rate(cid)` else `terms / V`; for a diluted species `rhs = -(S / V) * rate`, origin `dilution`; `Ode(..., size_rate=rate)`. Build the dilution with `node(libsbml.AST_TIMES, node(libsbml.AST_DIVIDE, name(sid), name(cid)), name(rate))` and the difference with `signed_sum([(1, terms_over_v), (-1, dilution)])`.
  - `_total_rate(sid, element, stack)`: a state: `self._resolved_rate(sid, element, stack)`; an assignment rule or a reaction id: the chain rule of its math with function definitions expanded (`libsbml.SBMLTransforms.replaceFD` on a copy), `None` if `derivative` returns `None` for any variable; `0` for a constant; a cycle (`sid in stack`) raises `ValueError("The rates of ... depend on each other in a cycle.")`. The chain rule: `signed_sum` of `derivative(f, TIME)` and `derivative(f, y) * _total_rate(y)` for `y in sorted(names(f))`, then `drop_zero_terms`.
  - `_rate_of(sid)`: a species in concentration is in `self.rhs` now; `rateOf(V)` of a compartment with an assignment rule is `name(self._size_rate(V))`; remove the amount branch.
  - `_build_assignments`: the size rates whose math is not `None` as `Assignment(rid, math, "size_rate")`, then the rules and reactions, `_ordered`.
  - `_initial_of`: remove the amount branches; the conversion branch (`initialAmount` of a concentration `n0 / V`, `initialConcentration` of an amount `c0 * V`) applies to every species; a diluted species is a state, so it gets its initial value.
  - `system()`: `OdeSystem(..., size_rates=tuple(SizeRate(symbol, cid, math) ...))`, no `amounts`.
- [ ] **Step 4**: the new tests pass; `uv run pytest tests/test_ode_system.py -q` and fix the tests of `test_ode_system.py` which assert amounts: each is rewritten to the native form (the state `S` instead of `n_S`, no assignment of origin `concentration`).
- [ ] **Step 5**: commit with Task 2: `git commit -am "Native quantities: concentrations stay states, the size rates dV/dt"`.

### Task 4: events which resize, and the code formats

**Files:**
- Modify: `src/sbmlode/analysis.py` (`_event_assignments`, `_rescaled`), `src/sbmlode/formats.py`, `src/sbmlode/templates/python.py.jinja`, `julia.jl.jinja`, `r.R.jinja`
- Test: `tests/test_ode_python.py`, `tests/test_ode_julia.py`, `tests/test_ode_r.py`, `tests/ode_helpers.py`

**Interfaces:**
- Produces: the code context of an event has `sizes`: `[{"id": cid, "index": j}]` (0-based), the function name `functions["sizes"]` (`event_sizes_<code>`, `None` without a divisor) and `scopes["sizes"]` (`math_scope([name(cid) ...])`); every assignment has `divisor_index` (the index into `sizes`, `None` without divisor), `divisor_position` is removed. The assignments of an event are ordered: those without divisor first.

- [ ] **Step 1: Write the failing test** `test_event_resizes_assigned_compartment` in `tests/test_ode_python.py`: a model like `variable_compartment.xml` whose event assigns `Va0 := 2` (so `Va` jumps); the python code simulated to t=5 equals roadrunner for `S2` (and the amount `S2 * Va` is continuous at the event).
- [ ] **Step 2**: run it, expected FAIL.
- [ ] **Step 3: Implement**:
  - `_rescaled(sid)`: a species in concentration (`not quantity.amount`) without an assignment rule of its own.
  - `_resized(event_assigned: set[str]) -> set[str]`: the compartments the event assigns, plus the compartments with an assignment rule whose rule depends transitively (through assignment rules and reaction rates, `names`) on a variable in `event_assigned`.
  - `_event_assignments`: for an assigned species in concentration whose compartment is resized: `EventAssignment(sid, math, name(cid), cid)`; for every other rescaled species of a resized compartment: `EventAssignment(sid, None, S * V, cid)`; the list sorted with `divisor is None` first; the special case of the amount (`self.amounts`) is removed.
  - `formats.py`: in `event`, `sizes = list(dict.fromkeys(a.divisor for a in event.assignments if a.divisor))`, `divisor_index = sizes.index(a.divisor)`; `functions["sizes"] = self.unique(f"event_sizes_{code}") if sizes else None`; `scopes["sizes"] = self.math_scope([name(c) for c in sizes])`; drop `amount_of` from the variables and the comment `amount of`; the docstring of the module lists the new keys.
  - templates (each language): a function `event_sizes_<code>(t, x, p)` which returns the sizes (`body(e.scopes.sizes)` then the array of the codes of `e.sizes`); in the assign function, after the assignments without divisor: `sizes = event_sizes(t, x, p)` with the new x and p, then the assignments with divisor `values[k] * scale / sizes[j]` (julia `sizes[j+1]`, R `sizes[[j+1]]`); the docstring of the assign function says "the size of a compartment which scales a value is the size before the event, the divisor the size after it".
  - `tests/ode_helpers.py`: `selection` without `amount_of`; `_rates` without `amount_of`.
- [ ] **Step 4**: `uv run pytest tests/test_ode_python.py -q`, then julia and R (`tox -e julia`, `tox -e r` or the pytest commands of `tox.ini`), fix the tests which assert amounts.
- [ ] **Step 5**: commit `"Events rescale every concentration of a resized compartment, with the size after the event"`.

### Task 5: the documents and the typeset target

**Files:**
- Modify: `src/sbmlode/documents.py`, `templates/latex.tex.jinja`, `typst.typ.jinja`, `markdown.md.jinja`, `docs/typeset.md`
- Test: `tests/test_ode_presentation.py`, `tests/test_ode_typeset.py`, `tests/golden/*`

**Interfaces:**
- Produces: `TypesetSystem` without `amounts`; `TypesetEventAssignment` without `species`, `conversion` is `None` or `resized`; the symbol of a size rate is `dialect.derivative` with the symbol of its compartment (`\frac{\mathrm{d}V}{\mathrm{d}t}`); `assignments` holds the origins `assignment_rule` and `size_rate`, a size rate of a compartment which is a state (rate rule) is left out (its ODE is in `odes`); `TypesetEquation.origin` of an ODE may be `dilution`.

- [ ] **Step 1: Write the failing test** in `tests/test_ode_typeset.py`: the typeset system of `variable_compartment.xml` has the ODE of `S1` whose last line ends with `\frac{\mathrm{d} \,\mathrm{Vc}}{\mathrm{d} t}` (or the plain form the dialect writes, assert on `\frac{\mathrm{d}` and `Vc`), an assignment of origin `size_rate` for `Va` and none for `Vc`, no field `amounts`; `wrap` is called with the symbol of the size rate whose `source` is `("Va",)`.
- [ ] **Step 2**: run, expected FAIL.
- [ ] **Step 3: Implement**: `_symbols` gives every size rate `self.dialect.derivative.replace("{symbol}", symbols[cid])` (with the thin space rule of `ode`); `ode()` appends the dilution: one line, print the whole `rhs`; several lines, the lines of `1/V (...)` and a last line `- \frac{S}{V} \cdot <rate>` printed from `node(AST_TIMES, node(AST_DIVIDE, S, V), rate)` with a leading minus; `event_assignment` without the amount branch; the templates lose the section of the amounts and describe the dilution in their sentences ("a species in concentration in a compartment whose size changes is diluted, see SBML L3V2 section 3.4.6"); the module docstring of `documents.py` updated.
- [ ] **Step 4**: regenerate the goldens with the script the tests name (`tests/golden/README` or the `--update-goldens` option of `test_ode_presentation.py`, check `rg -n "golden" tests/test_ode_presentation.py`), review the diff (only the amounts disappear in `events.*`/`demo.*`), run `uv run pytest -q -m "not sbml_testsuite"` and the document compilation tests of `tox -e documents`.
- [ ] **Step 5**: commit `"Documents: the dilution term and the size rates, no amounts"`.

### Task 6: the test suite, the documentation, the release notes

**Files:**
- Modify: `docs/formats.md`, `docs/index.md` (if it shows amounts), `README.md` (if it does), `release-notes/0.2.0.md` (new), `tests/test_ode_testsuite.py` (`KNOWN_FAILURES`, a named test of the variable compartment cases)
- Test: the sweeps

- [ ] **Step 1**: `uv run python scripts/ode_report.py > scratchpad/report_after.txt`; compare with `report_before.txt`: no case which passed fails; a newly passing case is a gain (remove it from `KNOWN_FAILURES` if listed). Every regression is fixed in Tasks 3 to 5 before going on.
- [ ] **Step 2**: the julia and R sweeps on the cases with variable compartments: `uv run python scripts/ode_report.py --format julia --format r --case 01506 --case 01779 ...` (the cases whose model has a compartment with a rule or an event assignment, found with `rg -l "compartment" ` over the cases is too broad: select with a small python snippet with libsbml over `semantic/*/*-sbml-l3v2.xml`).
- [ ] **Step 3**: `CURATED` gains three cases with variable compartments (rate rule, assignment rule, event); the docs describe the native quantities (`docs/formats.md` section on species, `docs/typeset.md` on `size_rate` and `dilution`), the docs images are regenerated if they show an amount (`scripts/docs_images.py`); `release-notes/0.2.0.md` lists the breaking changes and the new behavior; `uv run zensical build --clean --strict`.
- [ ] **Step 4**: full default run `uv run pytest -q`, ruff, ty; commit `"Native quantities: documentation, release notes, curated cases"`.
- [ ] **Step 5**: push the branch and open the PR (after confirmation with the user), CI green, merge; the version bump to 0.2.0 and the tag as `docs/development.md` of sbmlode describes, which publishes to PyPI.

## Part 2: sbml4humans

### Task 7: backend on sbmlode 0.2.0

**Files:**
- Modify: `backend/pyproject.toml`, `backend/uv.lock`, `backend/sbml4humans/model.py` (`OdeOrigin`), `backend/sbml4humans/report.py` (`ode_for_path`), `backend/sbml4humans/examples.py` (new example), `backend/sbml4humans/odes.py` (docstring)
- Create: `backend/sbml4humans/resources/examples/variable_compartment.xml` (the model of Task 3)
- Test: `backend/tests/test_odes.py`, `backend/tests/test_api.py` (or the files which test `ode_for_path`, `rg -l ode_for_path backend/tests`)

**Interfaces:**
- Produces: `OdeOrigin` = `reactions, rate_rule, dilution, assignment_rule, size_rate, initial_assignment, initial_value, reaction, function, event`; `ode_for_path(path, fmt, location=None, trusted=False, simulator=False)`.

- [ ] **Step 1**: dependency: `sbmlode>=0.2.0` once released; before the release `[tool.uv.sources] sbmlode = { path = "../../sbmlode", editable = true }` locally (not pushed to `develop`).
- [ ] **Step 2: Write the failing tests**: the report of the example `variable_compartment` has an `ode_system` whose `assignments` contain an equation of origin `size_rate` with `variable` the pk of `Va`; the ODE of `S1` has a `\htmlData{pk=` link to `Vc` in its last line; `ode_for_path(..., "python")` contains no `def simulate(` and `ode_for_path(..., "python", simulator=True)` does.
- [ ] **Step 3: Implement**: `OdeOrigin`; `ode_for_path` renders code formats with `render(fmt, simulator=simulator)` and documents with `render(fmt)` (`sbmlode.FORMATS[fmt].kind == "code"`); the example registered in `examples.py` like `species.xml` (description "compartments whose size changes: a rate rule, an assignment rule, an event"); regenerate `python -m sbml4humans.schema`.
- [ ] **Step 4**: `uv run pytest -q -x`, ruff, `ty check`.
- [ ] **Step 5**: commit `"Backend: sbmlode 0.2.0, the ODE system without simulator, an example of variable compartments"`.

### Task 8: the glossary

**Files:**
- Modify: `glossary/report.toml` (`equations`, `odeSystem`, `odeInitial`, `odeAssignments`, `odeDownload`, the origins), generated `frontend/src/data/glossary*.json`, `docs/reference/*.md`

- [ ] **Step 1**: read `glossary/CLAUDE.md`; edit the entries: `equations` lists the sections in the new order; `odeSystem` explains the native quantity and the dilution term with the formula of the spec; `odeInitial` label "initial assignments", text without "the amount the system integrates"; the origins `size_rate` ("rate of change of a size") and `dilution`, removing `concentration`; `odeDownload` says the files hold the ODE system only and that sbmlode writes custom exports (a simulator, names as symbols), with the link <https://matthiaskoenig.github.io/sbmlode/formats/>.
- [ ] **Step 2**: `uv run python -m sbml4humans.glossary` then `--check`; commit `"Glossary: native quantities, size rates, the code of the equations"`.

### Task 9: the frontend

**Files:**
- Modify: `frontend/package.json`, `package-lock.json` (`shiki`), `src/report/query.ts`, `src/report/view.ts`, `src/stores/report.ts`, `src/components/equations/EquationsView.vue`, `src/types/report.ts` (generated, `npm run types`)
- Create: `src/report/highlight.ts`, `src/components/equations/EquationTabs.vue`, `src/components/equations/EquationCode.vue`
- Delete: `src/components/equations/OdeDownload.vue`
- Test: `tests/unit/query.test.ts`, `tests/unit/reportStore.test.ts`, `tests/unit/equationsView.test.ts`, `tests/unit/highlight.test.ts` (new)

**Interfaces:**
- Consumes: `OdeFormat`, `store.downloadOde(format, location)`.
- Produces:
  - `ViewState.code: OdeFormat | null`, query key `code`, only with `view=equations`; `parseQuery` maps an unknown value to `null`.
  - `view.setCode(code: OdeFormat | null): Promise<unknown>`.
  - `store.odeCode(format: OdeFormat, location: string): Promise<OdeDownloadFile & { text: string }>`, cached per `${location}\n${format}` until the report changes; a rejected promise is removed from the cache.
  - `highlight(code: string, format: OdeFormat): Promise<string | null>`: the HTML of Shiki, `null` above `HIGHLIGHT_LIMIT = 200_000` characters (the component then shows the plain text).
  - `EquationTabs` props `{ code: OdeFormat | null }`, emits `select(code: OdeFormat | null)`; testids `equations-tab-math`, `equations-tab-<format>`.
  - `EquationCode` props `{ format: OdeFormat; location: string }`; testids `equations-code`, `equations-code-copy`, `equations-code-download`, `equations-code-help`, `equations-code-error`.

- [ ] **Step 1: Write the failing unit tests**:

```ts
// query.test.ts
it("keeps the format of the code of the equations", () => {
  const state = parseQuery({ view: "equations", code: "julia" });
  expect(state.code).toBe("julia");
  expect(toQuery(state)).toMatchObject({ view: "equations", code: "julia" });
});
it("reads an unknown format as the math", () => {
  expect(parseQuery({ view: "equations", code: "cobol" }).code).toBeNull();
});
it("drops the code outside of the equations", () => {
  expect(toQuery({ ...parseQuery({ code: "r" }), view: "tables" })).not.toHaveProperty("code");
});

// reportStore.test.ts
it("fetches the code of a format once per location", async () => { /* load a report with a fake ode download counting calls; odeCode twice -> one call; another location -> second call; a failing call is retried */ });

// highlight.test.ts
it("leaves a very long code plain", async () => {
  expect(await highlight("x = 1\n".repeat(50_000), "python")).toBeNull();
});
it("highlights python", async () => {
  expect(await highlight("x = 1", "python")).toContain("<pre");
});

// equationsView.test.ts
it("orders the sections from the definitions to the system", () => { /* mount with a system with every section, read the order of [data-testid^=equations-section-] */ });
```

- [ ] **Step 2**: `npx vitest run tests/unit/query.test.ts tests/unit/reportStore.test.ts tests/unit/highlight.test.ts tests/unit/equationsView.test.ts`; expected FAIL.
- [ ] **Step 3: Implement**:
  - `npm install shiki` (check the license MIT), `highlight.ts`:

```ts
import type { OdeFormat } from "@/api/client";

/** Above this length the code is shown plain: highlighting it would block the page. */
export const HIGHLIGHT_LIMIT = 200_000;

const LANGUAGES: Record<OdeFormat, string> = {
  python: "python", julia: "julia", r: "r", latex: "latex", typst: "typst", markdown: "markdown",
};

let highlighter: Promise<import("shiki/core").HighlighterCore> | null = null;

/** The highlighter of the six formats, created with the first code shown. */
function load(): Promise<import("shiki/core").HighlighterCore> {
  highlighter ??= (async () => {
    const { createHighlighterCore } = await import("shiki/core");
    const { createJavaScriptRegexEngine } = await import("shiki/engine/javascript");
    return createHighlighterCore({
      themes: [import("shiki/themes/github-light.mjs")],
      langs: [
        import("shiki/langs/python.mjs"), import("shiki/langs/julia.mjs"), import("shiki/langs/r.mjs"),
        import("shiki/langs/latex.mjs"), import("shiki/langs/typst.mjs"), import("shiki/langs/markdown.mjs"),
      ],
      engine: createJavaScriptRegexEngine(),
    });
  })();
  return highlighter;
}

/** The code as highlighted HTML, `null` for a code above `HIGHLIGHT_LIMIT`. Shiki escapes the code. */
export async function highlight(code: string, format: OdeFormat): Promise<string | null> {
  if (code.length > HIGHLIGHT_LIMIT) return null;
  return (await load()).codeToHtml(code, { lang: LANGUAGES[format], theme: "github-light" });
}
```

  - `query.ts`: `code` in `ViewState`, parsed with `isOdeFormat` (a set of the six formats, exported from `api/client.ts` next to `OdeFormat`), written only with `view === "equations"`; `view.ts`: `setCode`.
  - store: `odeCode` with a `Map<string, Promise<...>>` cleared in `load` and `clear`; the download file gains its text (`await blob.text()` once).
  - `EquationTabs.vue`: a `role="tablist"` row as in the prototype (`Math`, a separator, the formats with the names of the old `OdeDownload`), `aria-selected`, arrow keys move the focus and select, the classes of the prototype (border-b-2, blue for the selected).
  - `EquationCode.vue`: toolbar (file name in mono, Copy with "Copied" for 1.2 s via `navigator.clipboard.writeText`, Download via an object url as `OdeDownload` did, `HelpButton` of `odeDownload` with label "custom exports with sbmlode"), the code in `<div class="overflow-auto">` with `v-html` of `highlight`, else a `<pre>` of the plain text; loading text while the promise runs; `ErrorState` on failure; the `pre` of Shiki gets `text-xs leading-5 px-4 py-3`, no wrap.
  - `EquationsView.vue`: header with `EquationTabs` (`ml-auto`), `OdeDownload` removed; `SECTIONS` in the order `functions, assignments, reactions, odes, initial`, events after; each `EquationSection` gets `data-testid="equations-section-<field>"` (check `EquationSection.vue`, add the prop if needed); with `view.state.value.code` the `EquationCode` replaces the sections, the unsupported note stays above both.
  - delete `OdeDownload.vue`; `npm run types` after Task 7.
- [ ] **Step 4**: `npm run lint && npx vitest run && npm run build` (check that Shiki is a chunk of its own in the build output and the main chunk does not grow by more than a few kB).
- [ ] **Step 5**: commit `"Equations view: tabs of the math and the code of six formats, the sections from the definitions to the system"`.

### Task 10: e2e, fixtures, screenshots, documentation

**Files:**
- Modify: `frontend/tests/e2e/equations.spec.ts`, `frontend/tests/fixtures/*.json` (`npm run fixtures`), `frontend/scripts/screenshots.mjs`, `docs/images/report-equations.png`, new `docs/images/report-equations-code.png`, `docs/report.md`, `release-notes/<next version>.md`

- [ ] **Step 1: Write the e2e tests** (replace the download test):

```ts
test("the code of the equations in tabs, kept in the url", async ({ page }) => {
  await page.goto(`/examples/${REPRESSILATOR}?view=equations`);
  await expectReport(page);
  await page.getByTestId("equations-tab-julia").click();
  await expect(page).toHaveURL(/code=julia/);
  await expect(page.getByTestId("equations-code")).toContainText("function f_dxdt");
  await page.reload();
  await expect(page.getByTestId("equations-tab-julia")).toHaveAttribute("aria-selected", "true");
  await page.getByTestId("equations-tab-math").click();
  await expect(page).not.toHaveURL(/code=/);
});

test("the code downloads and copies without the simulator", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(`/examples/${REPRESSILATOR}?view=equations&code=python`);
  await expect(page.getByTestId("equations-code")).toContainText("def f_dxdt(");
  const downloading = page.waitForEvent("download");
  await page.getByTestId("equations-code-download").click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("BIOMD0000000012.py");
  const code = readFileSync((await download.path())!, "utf8");
  expect(code).toContain("def f_dxdt(");
  expect(code).not.toContain("def simulate(");
  await page.getByTestId("equations-code-copy").click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(code);
});

test("a concentration in a growing compartment is diluted", async ({ page }) => {
  await openExample(page, "variable_compartment (variable_compartment.xml)");
  await page.getByTestId("view-equations").click();
  const ode = page.locator('[data-equation-of$="Species:S1"]');
  await expect(ode.locator('[data-pk$="Compartment:Vc"]').first()).toBeVisible();
  await expect(page.getByTestId("equations-section-assignments")).toContainText("Va");
});
```

  and the algebraic rule test: the error of the python tab (`equations-code-error` contains "algebraic rule").
- [ ] **Step 2**: start the backend (`SBML4HUMANS_ALLOW_PRIVATE_URLS=1 uv run uvicorn sbml4humans.api:api --port 1444`) and run `npm run test:e2e`; fix until green; `npm run fixtures` and commit the regenerated fixtures.
- [ ] **Step 3**: screenshots: add a shot of the code tab to `scripts/screenshots.mjs`, run `npm run screenshots`, look at both images, `docs/report.md` describes the tabs and the native quantities; release notes of the next version (`release-notes/0.13.0.md`): native quantities, order, code tabs, downloads without simulator.
- [ ] **Step 4**: the full checks of `CLAUDE.md`: backend ruff, ty, pytest, schema diff, glossary check, release notes check, zensical build strict, frontend lint, vitest, build, e2e. Check the view in the browser at desktop and phone width, with chrome-devtools-axi.
- [ ] **Step 5**: commit; after the release of sbmlode 0.2.0, switch the dependency to the release, `uv lock`, push, PR (after confirmation with the user).

### Task 11: review

- [ ] Whole branch review of both repositories against the specs and the Review Focus, with `superpowers:requesting-code-review`; fix what it finds.
