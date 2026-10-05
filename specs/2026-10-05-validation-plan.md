# Validation in the Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every report carries the validation of libsbml (read errors and `checkConsistency()`), each issue attached to the element it concerns, and the frontend shows them as hints: chips in the app bar, a dot in the type bar, an icon in the table row, a block in the inspector and the list of all issues in the inspector of the document (#3).

**Architecture:** A new backend module `validation.py` validates a libsbml document, maps every issue to a pk by the start line and column which `SBMLDocumentInfo.sbase` records for every element, and installs `ReportResolver` into the resolver registry of libsbml so the comp validator only sees documents the report already read. `report._link` validates every entry once all are read and sets `Report.validation`. The frontend reads the issues through `ReportIndex` and renders them with a small `SeverityIcon` and two inspector components.

**Tech Stack:** Python 3.14, libsbml (SWIG, directors), FastAPI, pydantic, pytest, ruff, ty; Vue 3, TypeScript ~6.0.3, Tailwind 4, `@lucide/vue`, vitest, Playwright.

**Spec:** `specs/2026-10-05-validation-design.md` (read it first). Prototype: `.lavish/issue-3-validation.html` (git ignored), option C.

## Global Constraints

- Never use the em dash character anywhere; use a plain dash "-".
- No agent attribution anywhere: no Co-Authored-By lines, no "Generated with" lines in commits, PRs, code, docs.
- Never edit `CHANGELOG.md`, `docs/release-notes.md` or any generated file by hand (`frontend/src/types/*.ts`, `frontend/src/schema/*.json`, `frontend/src/data/glossary*.json`, `docs/reference/*.md`, `frontend/tests/fixtures/*.json` are generated).
- Markdown has no hard line wraps: one paragraph, list item or table row per line.
- Backend: every module, class and function is annotated and has a google style docstring; `uv run ruff check . && uv run ruff format --check . && uv run ty check` stay clean (ty warnings are errors, suppress only with `# ty: ignore[rule]`). Annotate libsbml objects explicitly and use the getters.
- Backend: logging through `logging.getLogger(__name__)` with lazy `%s` arguments, never configure logging.
- The error contract is unchanged: a document without a model is still answered by `error_response`.
- Validation never reads a file or url the content names: the comp validator only gets documents the report already read.
- Nothing of an issue is written by hand: `short_message`, `message`, `category` are the text of libsbml.
- Frontend: the words of the validation come from the concepts `validation`, `validationRule`, `validationSeverity`, `validationCategory` of `glossary/report.toml` (`conceptEntry(key)`); the remaining chrome ("more", "all categories", the empty message) stays in the components. Text is rendered as Vue text, never `v-html`. Every element an e2e test uses carries a `data-testid`. No new dependency.
- Components read the issues only through `ReportIndex`, never by building a pk.
- `develop` only takes pull requests: work on a branch `validation` and open a PR at the end.

## Review Focus

- A document with no lines on its elements (built in memory, `readSBMLFromString` of a one line file): every issue must still get a pk, the one of the document. Test in Task 1 (`test_one_line_document`).
- Two elements starting on the same line (a one line file, or several attributes on one line): an issue at the column of the second must go to the second, not the first. Test in Task 1 (`test_one_line_document`).
- An untrusted document whose external model definition names an existing absolute path or an http url: no file read, no request, 1090101 reported. Test in Task 2 (`test_untrusted_source_is_not_read`).
- A model with hundreds of issues (`random_network`, 435): the list must stay one line per rule and the tables must not slow down (the icon lookup is a `Map` get per row). Test in Task 4 (`groups by rule`) and Task 5 (the icon reads `worstSeverity`).
- A row of a windowed table (more than 200 rows) and the pinned id column of a narrow window: the icon must not change the row height or break the pinning. Checked in Task 7 with the screenshot of `random_network` at 360 px.

---

## File Structure

- Create `backend/sbml4humans/validation.py`: `ElementPositions`, `issues_of`, `ReportResolver`, `validate`. The only module which calls `checkConsistency`.
- Modify `backend/sbml4humans/model.py`: `Severity`, `ValidationIssue`, `Report.validation`.
- Modify `backend/sbml4humans/sbmlinfo.py`: `SBMLDocumentInfo.positions`, recorded in `sbase`.
- Modify `backend/sbml4humans/report.py`: `_link` validates every entry.
- Create `backend/sbml4humans/resources/examples/validation.xml`: the example with known issues.
- Create `backend/tests/test_validation.py`.
- Modify `glossary/report.toml`: four concepts.
- Generated: `frontend/src/schema/report.schema.json`, `frontend/src/types/report.ts`, `frontend/tests/fixtures/*.json` (plus `validation.json`), `frontend/src/data/glossary*.json`, `docs/reference/*.md`.
- Modify `frontend/scripts/fixtures.mjs`: the fixture `validation`.
- Modify `frontend/src/report/index.ts`: the issue lookups.
- Create `frontend/src/report/validation.ts`: grouping and severity order, pure functions.
- Create `frontend/src/components/misc/SeverityIcon.vue`.
- Create `frontend/src/components/inspector/ValidationBlock.vue` and `ValidationList.vue`.
- Create `frontend/src/components/report/ValidationSummary.vue`.
- Modify `frontend/src/components/report/ElementCell.vue`, `TypeBar.vue`, `ContextBar.vue`, `frontend/src/components/inspector/InspectorPanel.vue`.
- Tests: `frontend/tests/unit/validation.test.ts`, additions to `reportIndex.test.ts`, `typeBar.test.ts`, `inspector.test.ts`, `elementTable.test.ts`; `frontend/tests/e2e/validation.spec.ts`.
- Docs: `docs/report.md`, `docs/images/*` (retaken), `release-notes/0.11.0.md`.

---

### Task 0: Branch

- [ ] **Step 1: Create the branch from develop**

```bash
cd /home/mkoenig/git/sbml4humans && git switch -c validation
```

The spec commit `7d2d6a9` and the spec amendment are on local `develop`; they travel with the branch.

---

### Task 1: The model, the positions and the issues of a document

**Files:**
- Create: `backend/sbml4humans/validation.py`
- Create: `backend/sbml4humans/resources/examples/validation.xml`
- Modify: `backend/sbml4humans/model.py` (next to `Report`, around line 953)
- Modify: `backend/sbml4humans/sbmlinfo.py:255-268` (`__init__`) and `:370-425` (`sbase`)
- Test: `backend/tests/test_validation.py`

**Interfaces:**
- Produces: `model.Severity = Literal["error", "warning", "info"]`; `model.ValidationIssue(rule: int, severity: Severity, category: str, short_message: str, message: str, line: int, column: int, pk: str)`; `model.Report.validation: list[ValidationIssue] = []`.
- Produces: `SBMLDocumentInfo.positions: ElementPositions`, filled by every call of `sbase`.
- Produces: `validation.ElementPositions` with `add(sbase: libsbml.SBase, pk: str) -> None`, `pk_at(line: int, column: int) -> str`, constructed `ElementPositions(document_pk: str)`.
- Produces: `validation.issues_of(doc: libsbml.SBMLDocument, positions: ElementPositions) -> list[ValidationIssue]`: the whole error log of the document as it is now (no check run), mapped, duplicates dropped.

- [ ] **Step 1: Add the example**

Create `backend/sbml4humans/resources/examples/validation.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model metaid="meta_validation" id="validation" name="model with validation errors and warnings" substanceUnits="mole" timeUnits="second" volumeUnits="litre" extentUnits="mole">
    <notes>
      <body xmlns="http://www.w3.org/1999/xhtml">
        <p>Example model with an error and warnings of the validation of libsbml: the parameter x is set by an assignment rule and determined by an algebraic rule (overdetermined model), the compartment and the parameter k1 carry SBO terms of the wrong branch, and k1 and the literal numbers of the math declare no units.</p>
      </body>
    </notes>
    <listOfCompartments>
      <compartment id="cell" name="cell" sboTerm="SBO:0000009" spatialDimensions="3" size="1" units="litre" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="A" name="A" compartment="cell" initialAmount="10" substanceUnits="mole" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
      <species id="B" name="B" compartment="cell" initialAmount="0" substanceUnits="mole" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfParameters>
      <parameter id="k1" name="rate constant" sboTerm="SBO:0000236" value="0.1" constant="true"/>
      <parameter id="x" name="x" value="1" units="dimensionless" constant="false"/>
    </listOfParameters>
    <listOfRules>
      <assignmentRule variable="x">
        <math xmlns="http://www.w3.org/1998/Math/MathML"><cn type="integer"> 1 </cn></math>
      </assignmentRule>
      <algebraicRule>
        <math xmlns="http://www.w3.org/1998/Math/MathML"><apply><minus/><ci> x </ci><cn type="integer"> 1 </cn></apply></math>
      </algebraicRule>
    </listOfRules>
    <listOfReactions>
      <reaction id="R1" name="A to B" reversible="false">
        <listOfReactants>
          <speciesReference species="A" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="B" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply>
              <times/>
              <ci> k1 </ci>
              <ci> A </ci>
            </apply>
          </math>
        </kineticLaw>
      </reaction>
    </listOfReactions>
  </model>
</sbml>
```

Its issues with libsbml of `uv.lock` (probed 2026-10-05): `10712` warning line 10 (compartment), `10703`, `99508`, `20702` warnings line 17 (k1), `99505` warning line 21 (assignment rule) and line 36 (kinetic law), `10601` error line 3 (model).

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_validation.py`:

```python
"""Tests of the validation of a document and the mapping of its issues."""

import libsbml
import pytest

from sbml4humans.resources import EXAMPLES_DIR
from sbml4humans.sbmlinfo import SBMLDocumentInfo
from sbml4humans.validation import ElementPositions, issues_of


def _issues(source: str) -> list[tuple[int, str, str]]:
    """The rule, severity and pk of every issue of a document after the check."""
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(source))
    info.build_report()
    info.doc.checkConsistency()
    return [(i.rule, i.severity, i.pk) for i in issues_of(info.doc, info.positions)]


def _report_pks(info: SBMLDocumentInfo) -> list[str]:
    """The pk of every element of the report of a document."""
    pks: list[str] = []

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            if "pk" in obj and "sbmlType" in obj:
                pks.append(obj["pk"])
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(info.report.model_dump(by_alias=True))
    return pks


def test_example_issues_on_their_elements() -> None:
    """Every issue of the example goes to the element it concerns."""
    issues = _issues(str(EXAMPLES_DIR / "validation.xml"))
    by_rule: dict[int, set[str]] = {}
    for rule, _, pk in issues:
        by_rule.setdefault(rule, set()).add(pk)
    assert by_rule[10601] == {"validation/Model:validation"}
    assert by_rule[10712] == {"validation/Compartment:cell"}
    assert by_rule[10703] == by_rule[20702] == {"validation/Parameter:k1"}
    assert by_rule[99505] == {
        "validation/AssignmentRule:x",
        "validation/KineticLaw:R1.kineticLaw",
    }
    severities = {rule: severity for rule, severity, _ in issues}
    assert severities[10601] == "error"
    assert severities[10712] == "warning"


def test_valid_example_has_no_issues() -> None:
    """A valid document has no issues."""
    assert _issues(str(EXAMPLES_DIR / "species.xml")) == []


def test_read_errors_are_kept() -> None:
    """A read error stays in the log after the check and comes first."""
    sbml = (EXAMPLES_DIR / "minimal_model.xml").read_text()
    issues = _issues(sbml.replace("<model ", '<model foo="1" ', 1))
    assert issues[0][0] == 20222
    assert issues[0][1] == "error"
    assert issues[0][2] == "minimal_model/Model:minimal_model"


def test_duplicates_are_dropped() -> None:
    """An issue libsbml logs twice is one issue."""
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(str(EXAMPLES_DIR / "validation.xml")))
    info.build_report()
    info.doc.checkConsistency()
    log: libsbml.SBMLErrorLog = info.doc.getErrorLog()
    log.add(info.doc.getError(0))
    issues = issues_of(info.doc, info.positions)
    keys = [(i.rule, i.line, i.column, i.message) for i in issues]
    assert len(keys) == len(set(keys))


def test_one_line_document() -> None:
    """Elements on one line are told apart by their column, every issue has a pk."""
    sbml = " ".join((EXAMPLES_DIR / "validation.xml").read_text().split())
    issues = _issues(sbml)
    assert issues
    pks = {rule: pk for rule, _, pk in issues}
    assert pks[10712] == "validation/Compartment:cell"
    assert pks[10703] == "validation/Parameter:k1"


def test_position_before_every_element_is_the_document() -> None:
    """A position before the first element, or line 0, is the document."""
    positions = ElementPositions("document/SBMLDocument:document")
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(EXAMPLES_DIR / "species.xml"))
    model: libsbml.Model = doc.getModel()
    positions.add(model, "species/Model:species")
    assert positions.pk_at(0, 0) == "document/SBMLDocument:document"
    assert positions.pk_at(1, 1) == "document/SBMLDocument:document"
    assert positions.pk_at(model.getLine() + 1, 1) == "species/Model:species"


@pytest.mark.parametrize("name", ["comp_deletion.xml", "minimal_model_comp.xml"])
def test_comp_examples_map_every_issue(name: str) -> None:
    """Every issue of a comp example has a pk of the report."""
    info = SBMLDocumentInfo(SBMLDocumentInfo.read(str(EXAMPLES_DIR / name)))
    info.build_report()
    info.doc.checkConsistency()
    issues = issues_of(info.doc, info.positions)
    assert issues
    assert {i.pk for i in issues} <= set(_report_pks(info))
```

The pks are those of the report of the example (probed 2026-10-05): the document `document/SBMLDocument:document`, the model `validation/Model:validation`, `validation/Compartment:cell`, `validation/Parameter:k1`, `validation/AssignmentRule:x`, `validation/KineticLaw:R1.kineticLaw`. Check the pk of the model of `minimal_model.xml` used by `test_read_errors_are_kept` the same way.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_validation.py -q -x`
Expected: FAIL with `ModuleNotFoundError: No module named 'sbml4humans.validation'`.

- [ ] **Step 4: Add the model types**

In `backend/sbml4humans/model.py`, before `class Report(ReportModel)`:

```python
Severity = Literal["error", "warning", "info"]


class ValidationIssue(ReportModel):
    """An error, a warning or a note of the validation of libsbml.

    libsbml reports the line and the column of an issue, not its element: the
    pk is the element which starts closest before that position (the document
    when none does). The texts are those of libsbml.
    """

    rule: int
    severity: Severity
    category: str
    short_message: str
    message: str
    line: int
    column: int
    pk: str
```

and in `Report` add, after `link_graph`:

```python
    validation: list[ValidationIssue] = Field(default_factory=list)
```

(`Literal` and `Field` are already imported in `model.py`; check with `rg -n "^from typing|Field" backend/sbml4humans/model.py | head -3`.)

- [ ] **Step 5: Write `validation.py` with the positions and the issues**

Create `backend/sbml4humans/validation.py`:

```python
"""The validation of libsbml in the report.

libsbml reports an issue with its line and column, not with its element, so the
report records where every element starts (`ElementPositions`) and an issue
goes to the element which starts closest before it.
"""

import bisect
import logging

import libsbml

from sbml4humans.model import Severity, ValidationIssue


logger = logging.getLogger(__name__)

_ERRORS = frozenset(
    {libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL, libsbml.LIBSBML_SEV_SCHEMA_ERROR}
)
_WARNINGS = frozenset({libsbml.LIBSBML_SEV_WARNING, libsbml.LIBSBML_SEV_GENERAL_WARNING})


def _depth(sbase: libsbml.SBase) -> int:
    """How deep an element is nested below the document."""
    depth = 0
    parent: libsbml.SBase | None = sbase.getParentSBMLObject()
    while parent is not None:
        depth += 1
        parent = parent.getParentSBMLObject()
    return depth


class ElementPositions:
    """Where every element of a report starts in its file.

    Of two elements which start at the same position the one nested deeper
    wins, which is the element the position belongs to.
    """

    def __init__(self, document_pk: str) -> None:
        """Positions of no element yet; the document is where nothing starts."""
        self.document_pk = document_pk
        self._keys: list[tuple[int, int, int]] = []
        self._pks: list[str] = []

    def add(self, sbase: libsbml.SBase, pk: str) -> None:
        """Record the start of an element, ignoring an element without a line."""
        line = sbase.getLine()
        if line <= 0:
            return
        key = (line, sbase.getColumn(), _depth(sbase))
        index = bisect.bisect_right(self._keys, key)
        self._keys.insert(index, key)
        self._pks.insert(index, pk)

    def pk_at(self, line: int, column: int) -> str:
        """The pk of the element which starts closest at or before a position."""
        if line <= 0:
            return self.document_pk
        index = bisect.bisect_right(self._keys, (line, column, 1 << 30))
        return self._pks[index - 1] if index > 0 else self.document_pk


def _severity(error: libsbml.SBMLError) -> Severity:
    """The severity of the report for one of libsbml."""
    severity = error.getSeverity()
    if severity in _ERRORS:
        return "error"
    if severity in _WARNINGS:
        return "warning"
    return "info"


def issues_of(
    doc: libsbml.SBMLDocument, positions: ElementPositions
) -> list[ValidationIssue]:
    """The issues of the error log of a document, in its order, each once."""
    issues: list[ValidationIssue] = []
    seen: set[tuple[int, int, int, str]] = set()
    for k in range(doc.getNumErrors()):
        error: libsbml.SBMLError = doc.getError(k)
        line, column = error.getLine(), error.getColumn()
        message = error.getMessage().strip()
        key = (error.getErrorId(), line, column, message)
        if key in seen:
            continue
        seen.add(key)
        issues.append(
            ValidationIssue(
                rule=error.getErrorId(),
                severity=_severity(error),
                category=error.getCategoryAsString(),
                short_message=error.getShortMessage(),
                message=message,
                line=line,
                column=column,
                pk=positions.pk_at(line, column),
            )
        )
    return issues
```

The insertion with `bisect` keeps `add` cheap enough for 30000 elements (`insert` is a memmove); if a profile of `recon3d` shows it, collect unsorted and sort once in `pk_at` on first use instead.

- [ ] **Step 6: Record the positions in `SBMLDocumentInfo`**

In `sbmlinfo.py`, `__init__`, after `self.scope = DOCUMENT_SCOPE`:

```python
        # where every element of the report starts, for the issues of libsbml
        self.positions = ElementPositions(f"{DOCUMENT_SCOPE}/SBMLDocument:{DOCUMENT_SCOPE}")
```

Check that this pk is exactly the one `document()` builds (`sbmlinfo.py:634`: `pk=f"{DOCUMENT_SCOPE}/SBMLDocument:{DOCUMENT_SCOPE}"`); extract it into a module constant `DOCUMENT_PK` used by both, so they cannot drift.

In `sbase`, after the `pk` is computed (after the `elif key is None:` branch, before `xml = None`):

```python
        self.positions.add(sbase, pk)
```

Add `from sbml4humans.validation import ElementPositions` to the imports (`validation.py` imports only `model`, so there is no cycle).

- [ ] **Step 7: Run the tests and make them pass**

Run: `cd backend && uv run pytest tests/test_validation.py -q -x`
Expected: PASS (after the pk assertions are made exact as Step 2 says).

- [ ] **Step 8: Run the whole backend suite and the linters**

Run: `cd backend && uv run pytest -q -x && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: all pass. `test_examples.py` may count the examples; adjust its expected count for the new example if it does.

- [ ] **Step 9: Commit**

```bash
git add backend/sbml4humans/validation.py backend/sbml4humans/model.py backend/sbml4humans/sbmlinfo.py backend/sbml4humans/resources/examples/validation.xml backend/tests/test_validation.py backend/tests/test_examples.py
git commit -m "Issues of the validation of libsbml mapped to the elements of the report (#3)"
```

---

### Task 2: The resolver and the validation of every entry

**Files:**
- Modify: `backend/sbml4humans/validation.py`
- Modify: `backend/sbml4humans/report.py:167-177` (`_link`)
- Test: `backend/tests/test_validation.py`, `backend/tests/test_report.py`

**Interfaces:**
- Consumes: `issues_of`, `ElementPositions`, `SBMLDocumentInfo.positions`, `SBMLDocumentInfo.doc` (Task 1); `external.resolve_source(location, source)`, `external.normalize_location(location)`.
- Produces: `validation.validate(doc: libsbml.SBMLDocument, positions: ElementPositions, documents: Mapping[str, libsbml.SBMLDocument]) -> list[ValidationIssue]`: runs `checkConsistency()` with `documents` (keyed by the raw `source` of an external model definition) as the only documents the comp validator can resolve.
- Produces: `report._link` sets `entry.info.report.validation` of every entry.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_validation.py` (move the imports to the top of the module):

```python
import http.server
import threading

from sbml4humans.model import ReportResponse
from sbml4humans.report import report_for_bytes, report_for_path


COMP_DELETION = EXAMPLES_DIR / "comp_deletion.xml"


def _rules(response: ReportResponse, location: str | None = None) -> set[int]:
    """The rules of the issues of an entry of a response, the first by default."""
    entries = response.reports
    entry = entries[location] if location else next(iter(entries.values()))
    return {issue.rule for issue in entry.report.validation}


def test_untrusted_source_is_not_read() -> None:
    """An absolute path or a url of an untrusted document is never resolved."""
    requests: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            requests.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        target = (EXAMPLES_DIR / "unit_definitions.xml").resolve()
        sbml = COMP_DELETION.read_text()
        for source in (str(target), f"http://127.0.0.1:{server.server_port}/u.xml"):
            content = sbml.replace('comp:source="unit_definitions.xml"', f'comp:source="{source}"')
            response = report_for_bytes(content.encode())
            assert 1090101 in _rules(response), source
        assert requests == []
    finally:
        server.shutdown()


def test_untrusted_absolute_source_opens_no_file() -> None:
    """The resolver answers no absolute path, whatever libsbml asks."""
    import libsbml as _libsbml

    from sbml4humans.validation import validate

    target = (EXAMPLES_DIR / "unit_definitions.xml").resolve()
    sbml = COMP_DELETION.read_text().replace(
        'comp:source="unit_definitions.xml"', f'comp:source="{target}"'
    )
    doc: _libsbml.SBMLDocument = _libsbml.readSBMLFromString(sbml)
    issues = validate(doc, ElementPositions("d"), documents={})
    assert 1090101 in {i.rule for i in issues}


def test_trusted_neighbour_is_resolved_from_the_report() -> None:
    """A source the report read is resolved for the validation, without 1090101."""
    response = report_for_path(COMP_DELETION, trusted=True)
    assert 1090101 not in _rules(response, "./comp_deletion.xml")


def test_every_entry_is_validated() -> None:
    """The neighbour which a trusted file names is validated as well."""
    response = report_for_path(COMP_DELETION, trusted=True)
    assert len(response.reports) > 1
    for entry in response.reports.values():
        assert all(issue.pk for issue in entry.report.validation)


def test_resolver_delegates_outside_validation() -> None:
    """Outside of a validation libsbml resolves files as before."""
    import libsbml as _libsbml

    registry = _libsbml.SBMLResolverRegistry.getInstance()
    uri = (EXAMPLES_DIR / "unit_definitions.xml").resolve().as_uri()
    resolved = registry.resolveUri(uri, "")
    assert resolved is not None
```

Check the key of the master entry of a trusted single file with `uv run python -c "from sbml4humans.report import report_for_path; from sbml4humans.resources import EXAMPLES_DIR as E; print(list(report_for_path(E/'comp_deletion.xml', trusted=True).reports))"` and use it in place of `"./comp_deletion.xml"`. If `comp_deletion` still has 1090101 because its `md5` or `modelRef` does not match, pick the example whose external model definition the report resolves (`ResolutionStatus.resolved`, see `test_external.py`).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_validation.py -q -x -k "source or neighbour or entry or delegates"`
Expected: FAIL with `ImportError: cannot import name 'validate'` (and an empty `validation` list in the report tests).

- [ ] **Step 3: Add the resolver and `validate` to `validation.py`**

Append to `backend/sbml4humans/validation.py` (add `from collections.abc import Mapping` and `from contextvars import ContextVar` to the imports):

```python
# the documents the comp validator may resolve while a document is validated,
# keyed by the source of an external model definition, None outside of one
_DOCUMENTS: ContextVar[Mapping[str, libsbml.SBMLDocument] | None] = ContextVar(
    "validation_documents", default=None
)


class ReportResolver(libsbml.SBMLResolver):
    """The resolver of libsbml, confined to the report while it validates.

    The comp validator reads the document an external model definition names
    through the resolver registry of libsbml, which would read any path and,
    with a resolver for it, any url. While a document is validated this one
    answers only the documents of the report; at every other time it is the
    file resolver of libsbml.
    """

    def __init__(self) -> None:
        """A resolver which keeps the file resolver of libsbml to delegate to."""
        super().__init__()
        self._files = libsbml.SBMLFileResolver()

    def resolve(self, uri: str, baseUri: str = "") -> libsbml.SBMLDocument | None:  # noqa: N803
        """The document at a uri: one of the report while validating."""
        documents = _DOCUMENTS.get()
        if documents is None:
            return self._files.resolve(uri, baseUri)
        doc = documents.get(uri)
        if doc is None:
            return None
        # the caller of a resolver owns the document it returns
        clone: libsbml.SBMLDocument = doc.clone()
        clone.thisown = False
        return clone

    def resolveUri(self, uri: str, baseUri: str = "") -> libsbml.SBMLUri | None:  # noqa: N802, N803
        """The uri of a document: one of the report while validating."""
        documents = _DOCUMENTS.get()
        if documents is None:
            return self._files.resolveUri(uri, baseUri)
        if uri not in documents:
            return None
        resolved = libsbml.SBMLUri(uri)
        resolved.thisown = False
        return resolved

    def clone(self) -> "ReportResolver":
        """The registry keeps the one instance, so a clone is the instance."""
        return self


def _install_resolver() -> ReportResolver:
    """Replace the resolvers of the registry of libsbml by the report resolver."""
    registry = libsbml.SBMLResolverRegistry.getInstance()
    while registry.getNumResolvers() > 0:
        registry.removeResolver(0)
    resolver = ReportResolver()
    registry.addResolver(resolver)
    return resolver


# kept referenced, so that python does not collect the director libsbml calls
_RESOLVER = _install_resolver()


def validate(
    doc: libsbml.SBMLDocument,
    positions: ElementPositions,
    documents: Mapping[str, libsbml.SBMLDocument],
) -> list[ValidationIssue]:
    """Check the consistency of a document and return all of its issues.

    `documents` are the documents of the report which the external model
    definitions of the document name, keyed by their `source`: the only ones
    the comp validator can read.
    """
    token = _DOCUMENTS.set(documents)
    try:
        doc.checkConsistency()
    finally:
        _DOCUMENTS.reset(token)
    return issues_of(doc, positions)
```

Verify the director survives `addResolver`: libsbml's `addResolver` stores a clone (`resolver->clone()`); because `clone` returns `self`, the registry holds the Python object. If `addResolver` copies on the C++ side and the director is lost (the test `test_untrusted_absolute_source_opens_no_file` then fails with 0 issues of 1090101 and a file read in `strace`), set `resolver.thisown = False` before `addResolver` and keep `_RESOLVER`. The probe of 2026-10-05 (`res4.py`, `res5.py` in the session scratchpad) worked with exactly this class.

- [ ] **Step 4: Validate every entry in `report._link`**

In `backend/sbml4humans/report.py`, add `from sbml4humans.validation import validate`, and at the end of `_link`:

```python
    for location, entry in entries.items():
        entry.info.report.validation = validate(
            entry.info.doc,
            entry.info.positions,
            _documents_of(location, entry, entries),
        )
```

and the helper below `_link`:

```python
def _documents_of(
    location: str, entry: _Entry, entries: dict[str, _Entry]
) -> dict[str, libsbml.SBMLDocument]:
    """The documents of the report which the external model definitions name.

    Keyed by the source as the definition writes it, which is what the comp
    validator asks the resolver for; a source which names no entry is left out
    and stays unresolved.
    """
    by_location = {normalize_location(loc): other for loc, other in entries.items()}
    documents: dict[str, libsbml.SBMLDocument] = {}
    for emd in entry.info.report.external_model_definitions:
        target = by_location.get(resolve_source(location, emd.source))
        if target is not None:
            documents[emd.source] = target.info.doc
    return documents
```

with `import libsbml` at the top of `report.py`. `emd.source` is the `source` field of the report's `ExternalModelDefinition` (check the field name with `rg -n "class ExternalModelDefinition" -A12 backend/sbml4humans/model.py`).

Validation mutates the error log of `entry.info.doc` only, so the order of the entries does not matter.

- [ ] **Step 5: Run the tests**

Run: `cd backend && uv run pytest tests/test_validation.py tests/test_report.py tests/test_external.py -q -x`
Expected: PASS.

- [ ] **Step 6: Check the time of a large report**

Run: `cd backend && uv run python -c "import time; from sbml4humans.report import report_for_path; from sbml4humans.resources import EXAMPLES_DIR as E; t=time.time(); r=report_for_path(E/'random_network.xml'); print(time.time()-t, len(next(iter(r.reports.values())).report.validation))"`
Expected: well under a second, 435 issues. Also time the largest curated biomodel in `BIOMODELS_CURATED_PATH`; if validation adds more than 20 % to its report time, note it in the PR.

- [ ] **Step 7: Run the whole backend suite and the linters**

Run: `cd backend && uv run pytest -q -x && uv run ruff check . && uv run ruff format --check . && uv run ty check`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add backend/sbml4humans/validation.py backend/sbml4humans/report.py backend/tests/test_validation.py
git commit -m "Validate every entry against the documents of the report only (#3)"
```

---

### Task 3: Schema, types, fixtures and glossary

**Files:**
- Modify: `glossary/report.toml` (append after `[concepts.targetEntry]`)
- Modify: `frontend/scripts/fixtures.mjs` (the map of fixture names, around line 21)
- Generated: `frontend/src/schema/report.schema.json`, `frontend/src/types/report.ts`, `frontend/tests/fixtures/*.json`, `frontend/src/data/glossary.json`, `frontend/src/data/glossary-details.json`, `docs/reference/*.md`

**Interfaces:**
- Produces: TS types `ValidationIssue { rule: number; severity: "error" | "warning" | "info"; category: string; shortMessage: string; message: string; line: number; column: number; pk: string }`, `Report.validation?: ValidationIssue[]` (check the exact generated names in `report.ts` and use them below).
- Produces: concepts `validation`, `validationRule`, `validationSeverity`, `validationCategory`.
- Produces: fixture `validation` (`loadReport("validation")`).

- [ ] **Step 1: Add the concepts**

Append to `glossary/report.toml`:

```toml
[concepts.validation]
label = "validation"
summary = "the errors and warnings libsbml finds in the document"
description = """
The report runs the consistency checks of [libsbml](https://sbml.org/software/libsbml/) on every document with the categories libsbml checks by default: the identifiers, the general rules of the specification and of its packages, the SBO terms, the math, the units, whether the model is overdetermined and the modelling practice. The errors libsbml finds while it reads the file are part of it too.

libsbml checks in stages and stops after the first stage which finds an error, so a document with an error of its identifiers shows none of its unit warnings until that error is fixed.

libsbml reports where in the file an issue is, not which element it concerns, so the report gives an issue to the element which starts closest before that position, and to the document when none does. For a document of the comp package libsbml instantiates the submodels to check them and says itself that its line numbers are unreliable: the element of such an issue can be the wrong one.

The external model definitions are checked against the documents which are part of the report; the validation reads no other file and fetches no url.
"""

[concepts.validationRule]
label = "rule"
summary = "the number of the validation rule of libsbml"
description = """
Every issue names the rule it breaks by its number in libsbml. A rule of SBML core has a number below 100000 and is one of the validation rules of the appendix of the specification, a number of 99000 and above is a check of libsbml of its own, and a rule of a package carries the offset of the package. Where the glossary cites a rule, its text is part of the explanation of the element in the help.
"""

[concepts.validationSeverity]
label = "severity"
summary = "whether an issue is an error, a warning or a note"
description = """
- `error`: the document breaks a rule the specification requires; a tool may refuse or misread it.
- `warning`: the document follows the rules, but something is likely not what was meant, such as a quantity without units.
- `info`: a note of libsbml, which needs no change.
"""

[concepts.validationCategory]
label = "category"
summary = "which check of libsbml found the issue"
description = """
libsbml groups its checks in categories, such as the unit consistency, the identifier consistency or the consistency of a package. The list of all issues can be filtered by them.
"""
```

Check the description for links: `glossary --check` fails on a link which does not resolve; an absolute url is fine. Keep every paragraph on one line.

- [ ] **Step 2: Add the fixture**

In `frontend/scripts/fixtures.mjs`, add to the map next to `comp_deletion`:

```js
  validation: "validation (validation.xml)",
```

and add `"validation"` to the `FixtureName` type in `frontend/tests/unit/fixtures.ts` if it lists the names (check with `rg -n "FixtureName" frontend/tests/unit/fixtures.ts`).

- [ ] **Step 3: Regenerate everything**

Run from the repository root, with the backend running on 1444 for the fixtures (`cd backend && SBML4HUMANS_ALLOW_PRIVATE_URLS=1 uv run uvicorn sbml4humans.api:api --port 1444` in the background via the harness):

```bash
cd backend && uv run python -m sbml4humans.schema && uv run python -m sbml4humans.glossary && cd ../frontend && npm run types && npm run fixtures
```

Expected: `report.schema.json` gains `ValidationIssue`, `report.ts` gains the interface, every fixture gains `validation`, `tests/fixtures/validation.json` exists, the glossary outputs gain the four concepts.

- [ ] **Step 4: Run the checks**

Run: `cd backend && uv run python -m sbml4humans.glossary --check && uv run pytest tests/test_schema.py tests/test_glossary.py -q -x && cd ../frontend && npm run build && npx vitest run -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add glossary/report.toml frontend/scripts/fixtures.mjs frontend/tests/unit/fixtures.ts frontend/src/schema frontend/src/types frontend/tests/fixtures frontend/src/data docs/reference
git commit -m "Schema, types, fixtures and the glossary of the validation (#3)"
```

---

### Task 4: ReportIndex lookups and grouping

**Files:**
- Modify: `frontend/src/report/index.ts`
- Create: `frontend/src/report/validation.ts`
- Test: `frontend/tests/unit/reportIndex.test.ts`, `frontend/tests/unit/validation.test.ts`

**Interfaces:**
- Consumes: `ValidationIssue`, `Report.validation` (Task 3, import from `@/api/types` as `index.ts` does; re-export `ValidationIssue` there if `api/types.ts` lists the types explicitly).
- Produces in `report/validation.ts`: `type Severity = ValidationIssue["severity"]`; `SEVERITY_ORDER: readonly Severity[] = ["error", "warning", "info"]`; `worse(a: Severity | null, b: Severity): Severity`; `interface IssueGroup { rule: number; severity: Severity; category: string; shortMessage: string; issues: ValidationIssue[] }`; `groupByRule(issues: readonly ValidationIssue[]): IssueGroup[]` (errors first, then by rule number).
- Produces on `ReportIndex`: `readonly issues: readonly ValidationIssue[]`; `issuesOf(pk: string): ValidationIssue[]` (errors first, stable); `worstSeverity(pk: string): Severity | null`; `issueCounts: Record<Severity, number>`; `worstSeverityOfType(type: ElementType): Severity | null` (over the elements of every model of the entry whose `sbmlType` is the type).

- [ ] **Step 1: Write the failing tests**

Create `frontend/tests/unit/validation.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import type { ValidationIssue } from "@/api/types";
import { groupByRule, worse } from "@/report/validation";

function issue(rule: number, severity: ValidationIssue["severity"], pk: string): ValidationIssue {
  return { rule, severity, category: "c", shortMessage: `m${rule}`, message: "", line: 1, column: 1, pk };
}

describe("validation", () => {
  it("groups by rule, errors first", () => {
    const groups = groupByRule([
      issue(20513, "warning", "a"),
      issue(10601, "error", "b"),
      issue(20513, "warning", "c"),
      issue(99505, "warning", "d"),
    ]);
    expect(groups.map((g) => g.rule)).toEqual([10601, 20513, 99505]);
    expect(groups[1]?.issues.map((i) => i.pk)).toEqual(["a", "c"]);
  });

  it("keeps hundreds of issues of one rule to one group", () => {
    const many = Array.from({ length: 435 }, (_, k) => issue(99508, "warning", `p${k}`));
    expect(groupByRule(many)).toHaveLength(1);
  });

  it("orders severities", () => {
    expect(worse(null, "info")).toBe("info");
    expect(worse("warning", "error")).toBe("error");
    expect(worse("error", "warning")).toBe("error");
  });
});
```

Append to `frontend/tests/unit/reportIndex.test.ts` (inside the `describe`, with `const validation = new ReportIndex(loadReport("validation"));` next to the other indexes):

```ts
  it("looks up the issues of an element and of a type", () => {
    const k1 = validation.mainModel?.parameters?.find((p) => p.id === "k1");
    expect(k1).toBeDefined();
    expect(validation.issuesOf(k1!.pk).map((i) => i.rule)).toEqual(
      expect.arrayContaining([10703, 20702]),
    );
    expect(validation.worstSeverity(k1!.pk)).toBe("warning");
    expect(validation.worstSeverity(validation.mainModel!.pk)).toBe("error");
    expect(validation.issueCounts.error).toBe(1);
    expect(validation.issueCounts.warning).toBeGreaterThan(3);
    expect(validation.worstSeverityOfType("Parameter")).toBe("warning");
    expect(validation.worstSeverityOfType("Species")).toBeNull();
    expect(repressilator.issuesOf(repressilator.document.pk)).toEqual([]);
  });
```

Check the field name of the parameters of a model (`rg -n "parameters" frontend/src/types/report.ts | head -3`) and adjust.

- [ ] **Step 2: Run to verify they fail**

Run: `cd frontend && npx vitest run tests/unit/validation.test.ts tests/unit/reportIndex.test.ts`
Expected: FAIL, `@/report/validation` not found and `issuesOf` is not a function.

- [ ] **Step 3: Write `report/validation.ts`**

```ts
import type { ValidationIssue } from "@/api/types";

export type Severity = ValidationIssue["severity"];

/** The severities from the worst to the mildest, the order of every list of issues. */
export const SEVERITY_ORDER: readonly Severity[] = ["error", "warning", "info"];

const RANK: Record<Severity, number> = { error: 0, warning: 1, info: 2 };

/** The worse of two severities, where null is no issue at all. */
export function worse(a: Severity | null, b: Severity): Severity {
  return a === null || RANK[b] < RANK[a] ? b : a;
}

/** The issues sorted errors first, in their order otherwise. */
export function bySeverity(issues: readonly ValidationIssue[]): ValidationIssue[] {
  return [...issues].sort((a, b) => RANK[a.severity] - RANK[b.severity]);
}

/** The issues of one rule: the list of all issues shows a rule once, with its elements. */
export interface IssueGroup {
  rule: number;
  severity: Severity;
  category: string;
  shortMessage: string;
  issues: ValidationIssue[];
}

/** The issues grouped by rule, errors first, then by the number of the rule. */
export function groupByRule(issues: readonly ValidationIssue[]): IssueGroup[] {
  const groups = new Map<number, IssueGroup>();
  for (const issue of issues) {
    const group = groups.get(issue.rule);
    if (group) {
      group.issues.push(issue);
      group.severity = worse(group.severity, issue.severity);
    } else {
      groups.set(issue.rule, {
        rule: issue.rule,
        severity: issue.severity,
        category: issue.category,
        shortMessage: issue.shortMessage,
        issues: [issue],
      });
    }
  }
  return [...groups.values()].sort(
    (a, b) => RANK[a.severity] - RANK[b.severity] || a.rule - b.rule,
  );
}
```

- [ ] **Step 4: Add the lookups to `ReportIndex`**

In `frontend/src/report/index.ts`, import `ValidationIssue` with the other types and `{ bySeverity, worse, type Severity } from "@/report/validation"`. Add fields:

```ts
  /** The issues of the validation of the document, in the order of libsbml. */
  readonly issues: readonly ValidationIssue[];
  private readonly issuesByPk = new Map<string, ValidationIssue[]>();
  private readonly worstByPk = new Map<string, Severity>();
  readonly issueCounts: Record<Severity, number> = { error: 0, warning: 0, info: 0 };
```

At the end of the constructor:

```ts
    this.issues = report.validation ?? [];
    for (const issue of this.issues) {
      push(this.issuesByPk, issue.pk, issue);
      this.worstByPk.set(issue.pk, worse(this.worstByPk.get(issue.pk) ?? null, issue.severity));
      this.issueCounts[issue.severity] += 1;
    }
```

(`readonly issues` is assigned in the constructor, declare it without an initializer.) Methods:

```ts
  /** The issues of an element, errors first. */
  issuesOf(pk: string): ValidationIssue[] {
    return bySeverity(this.issuesByPk.get(pk) ?? []);
  }

  /** The worst severity of the issues of an element, null without one. */
  worstSeverity(pk: string): Severity | null {
    return this.worstByPk.get(pk) ?? null;
  }

  /** The worst severity of the elements of a type in every model of the entry. */
  worstSeverityOfType(type: ElementType): Severity | null {
    let worst: Severity | null = null;
    for (const [pk, severity] of this.worstByPk) {
      if (this.elements.get(pk)?.sbmlType === type) worst = worse(worst, severity);
    }
    return worst;
  }
```

`worstSeverityOfType` iterates the elements with issues only (435 at most for the examples), called once per type of the type bar inside a `computed`.

- [ ] **Step 5: Run the tests**

Run: `cd frontend && npx vitest run tests/unit/validation.test.ts tests/unit/reportIndex.test.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/report/index.ts frontend/src/report/validation.ts frontend/tests/unit/validation.test.ts frontend/tests/unit/reportIndex.test.ts
git commit -m "ReportIndex: the issues of an element, of a type and of the document (#3)"
```

---

### Task 5: Hints in the app bar, the type bar and the tables

**Files:**
- Create: `frontend/src/components/misc/SeverityIcon.vue`
- Create: `frontend/src/components/report/ValidationSummary.vue`
- Modify: `frontend/src/components/report/ContextBar.vue` (after `document-info`, line ~50)
- Modify: `frontend/src/components/report/TypeBar.vue` (after `bar-count-${info.type}`, line ~170)
- Modify: `frontend/src/components/report/ElementCell.vue:67-78` (the id cell)
- Test: `frontend/tests/unit/typeBar.test.ts`, `frontend/tests/unit/elementTable.test.ts`, `frontend/tests/unit/appBar.test.ts` or a new `validationSummary.test.ts`

**Interfaces:**
- Consumes: `ReportIndex.issueCounts`, `worstSeverity(pk)`, `issuesOf(pk)`, `worstSeverityOfType(type)`; `useReportView().select(pk)`; `conceptEntry("validation")`.
- Produces: `SeverityIcon` with props `{ severity: Severity; size?: "sm" | "md" }`, renders `data-testid="severity-${severity}"`.
- Produces: `ValidationSummary` with prop `{ index: ReportIndex }`, `data-testid="validation-summary"`, chips `validation-errors` and `validation-warnings`.

- [ ] **Step 1: Write the failing tests**

Look at the mounting helpers of `tests/unit/typeBar.test.ts` and `tests/unit/elementTable.test.ts` (`rg -n "mount\(|function render|provide" frontend/tests/unit/typeBar.test.ts | head`) and add, in their style:

- `typeBar.test.ts`: mounted with `new ReportIndex(loadReport("validation"))`, `bar-type-Parameter` contains `[data-testid="severity-warning"]`, `bar-type-Species` contains none.
- `elementTable.test.ts`: the row of `k1` of the validation fixture contains `[data-testid="row-issue"]` with `severity-warning`; the row of species `A` contains none; the tooltip text of `row-issue` contains `10703`.
- `validationSummary.test.ts` (new, mount `ValidationSummary` with the index of the validation fixture and the router of `tests/unit/view.test.ts`): `validation-errors` has text `1` plus the error word, `validation-warnings` shows the count of `index.issueCounts.warning`; a click on `validation-errors` sets the route query `pk` to `index.document.pk`; mounted with the repressilator index, `validation-summary` does not exist.

Write each as a concrete `it(...)` with `expect(wrapper.find(...).exists()).toBe(...)` assertions.

- [ ] **Step 2: Run to verify they fail**

Run: `cd frontend && npx vitest run tests/unit/typeBar.test.ts tests/unit/elementTable.test.ts tests/unit/validationSummary.test.ts`
Expected: FAIL.

- [ ] **Step 3: `SeverityIcon.vue`**

```vue
<script setup lang="ts">
import { CircleAlertIcon, InfoIcon, TriangleAlertIcon } from "@lucide/vue";
import { computed } from "vue";

import type { Severity } from "@/report/validation";

/** The mark of a severity: red for an error, amber for a warning, gray for a note. */
const props = withDefaults(defineProps<{ severity: Severity; size?: "sm" | "md" }>(), {
  size: "sm",
});

const icon = computed(
  () => ({ error: CircleAlertIcon, warning: TriangleAlertIcon, info: InfoIcon })[props.severity],
);
const color = computed(
  () => ({ error: "text-red-600", warning: "text-amber-500", info: "text-gray-400" })[props.severity],
);
</script>

<template>
  <component
    :is="icon"
    :class="[color, size === 'sm' ? 'size-3.5' : 'size-4']"
    class="shrink-0"
    :aria-label="severity"
    role="img"
    :data-testid="`severity-${severity}`"
  />
</template>
```

Check the icon names exist in `@lucide/vue` (`ls frontend/node_modules/@lucide/vue/dist/esm/icons | grep -E "circle-alert|triangle-alert|^info"`).

- [ ] **Step 4: The icon in the id cell**

In `ElementCell.vue`, import `SeverityIcon` and `useReportIndex` is already there (`index`). Add:

```ts
/** The worst severity of the issues of the row, which its id cell marks; a note alone is no mark. */
const severity = computed(() => {
  if (props.column.kind !== "id") return null;
  const worst = index.value?.worstSeverity(props.row.pk) ?? null;
  return worst === "info" ? null : worst;
});
const issueTip = computed(() =>
  severity.value
    ? (index.value?.issuesOf(props.row.pk) ?? [])
        .map((issue) => `${issue.rule} ${issue.shortMessage}`)
        .join("\n")
    : undefined,
);
```

and in the template, as the first child of the id `span` (before `TypeMark`):

```vue
    <span v-if="severity" v-tooltip="issueTip" class="flex" data-testid="row-issue">
      <SeverityIcon :severity="severity" />
    </span>
```

The icon is 14 px in a row of 1.5rem line height: the row height does not change, also not in a windowed table (`ROW_HEIGHT`). Check `v-tooltip` keeps the newlines (`rg -n "white-space|pre-line" frontend/src/directives`); if not, join with `" · "`.

- [ ] **Step 5: The dot of the type bar**

In `TypeBar.vue`, script:

```ts
const severityOf = (type: ElementType) => {
  const worst = props.index.worstSeverityOfType(type);
  return worst === "info" ? null : worst;
};
```

template, after the `bar-count` span:

```vue
        <SeverityIcon
          v-if="severityOf(info.type)"
          :severity="severityOf(info.type)!"
          :data-testid="`bar-issue-${info.type}`"
        />
```

(If a `data-testid` on the component replaces the inner one, assert on `bar-issue-...` plus `severity-...` via `find("svg")` instead; Vue passes the attribute through to the root, so the inner `severity-` testid is overwritten: pass the type test id on a wrapping `span` instead.)

- [ ] **Step 6: `ValidationSummary.vue` in the context bar**

```vue
<script setup lang="ts">
import { computed } from "vue";

import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { conceptEntry } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";

/** The counts of the errors and the warnings of the document; a click opens their list, which
 * is the inspector of the document. A valid document shows nothing. */
const props = defineProps<{ index: ReportIndex }>();
const view = useReportView();
const counts = computed(() => props.index.issueCounts);
const tooltip = computed(() => conceptEntry("validation")?.summary);
</script>

<template>
  <span
    v-if="counts.error + counts.warning > 0"
    class="flex shrink-0 items-center gap-1"
    data-testid="validation-summary"
  >
    <button
      v-if="counts.error > 0"
      v-tooltip.bottom="tooltip"
      type="button"
      class="flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-xs text-red-700 hover:bg-red-100"
      data-testid="validation-errors"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="error" />{{ counts.error }}<span class="max-md:hidden">error{{ counts.error === 1 ? "" : "s" }}</span>
    </button>
    <button
      v-if="counts.warning > 0"
      v-tooltip.bottom="tooltip"
      type="button"
      class="flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-700 hover:bg-amber-100"
      data-testid="validation-warnings"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="warning" />{{ counts.warning }}<span class="max-md:hidden">warning{{ counts.warning === 1 ? "" : "s" }}</span>
    </button>
  </span>
</template>
```

"error" and "warning" are the values of `validationSeverity` which its description lists, the words of libsbml; they are chrome of the chip like "more". In `ContextBar.vue` render `<ValidationSummary :index="index" />` right after the `document-info` span. Check on a 360 px window (Task 7) that the bar still fits: the words are `max-md:hidden`, the counts stay.

- [ ] **Step 7: Run the tests, the build and the lint**

Run: `cd frontend && npx vitest run && npm run build && npm run lint`
Expected: PASS (check the lint script name with `grep -n '"lint' package.json`).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components frontend/tests/unit
git commit -m "Validation hints in the app bar, the type bar and the id of a row (#3)"
```

---

### Task 6: The inspector: the block of an element and the list of the document

**Files:**
- Create: `frontend/src/components/inspector/ValidationBlock.vue`
- Create: `frontend/src/components/inspector/ValidationList.vue`
- Modify: `frontend/src/components/inspector/InspectorPanel.vue` (inside the first column, above `Attributes`, line ~146)
- Test: `frontend/tests/unit/inspector.test.ts`

**Interfaces:**
- Consumes: `ReportIndex.issuesOf`, `issues`, `document`; `groupByRule`, `SEVERITY_ORDER`; `conceptEntry`; `SeverityIcon`; `ElementLink` (`frontend/src/components/misc/ElementLink.vue`, props `pk`, `label`, check with `rg -n "defineProps" frontend/src/components/misc/ElementLink.vue`); `HelpLabel` (`help-key`, `tooltip`), the concept help keys `concepts/validation` etc. (check how `conceptEntry` keys map to help keys with `rg -n "concepts/" frontend/src/report/glossary.ts`).
- Produces: `ValidationBlock` with props `{ issues: ValidationIssue[] }`, `data-testid="inspector-validation"`; `ValidationList` with props `{ index: ReportIndex }`, `data-testid="validation-list"`, groups `validation-group`, filters `validation-filter-${severity}` (checkbox) and `validation-filter-category` (select).

- [ ] **Step 1: Write the failing tests**

In `tests/unit/inspector.test.ts`, with the validation fixture, following its mount helper:

- inspecting `k1`: `inspector-validation` exists, holds 4 issues (`10703`, `99508`, `20702` and their short messages), each with `severity-warning`; inspecting species `A`: no `inspector-validation`.
- the "more" `details` of an issue contains its full `message`.
- inspecting the document: `validation-list` exists; its `validation-group` items start with `10601` (the error), the group of `99505` shows `2`; unchecking `validation-filter-warning` leaves only the `10601` group; selecting a category in `validation-filter-category` leaves only groups of that category.
- inspecting the repressilator document: `validation-list` shows the empty message (`no-validation-issues`).
- clicking the element link of the `10712` group sets the route `pk` to the compartment.

- [ ] **Step 2: Run to verify they fail**

Run: `cd frontend && npx vitest run tests/unit/inspector.test.ts`
Expected: FAIL.

- [ ] **Step 3: `ValidationBlock.vue`**

```vue
<script setup lang="ts">
import type { ValidationIssue } from "@/api/types";
import HelpLabel from "@/components/help/HelpLabel.vue";
import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { conceptEntry } from "@/report/glossary";

/** The issues of one element: the short message, the rule, the category and the severity, the
 * full message of libsbml behind "more". */
defineProps<{ issues: ValidationIssue[] }>();
const validation = conceptEntry("validation");
const rule = conceptEntry("validationRule");
const BOX = {
  error: "border-red-200 bg-red-50",
  warning: "border-amber-200 bg-amber-50",
  info: "border-gray-200 bg-gray-50",
} as const;
</script>

<template>
  <section v-if="issues.length" class="mb-3" data-testid="inspector-validation">
    <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
      <HelpLabel help-key="concepts/validation" :tooltip="validation?.summary">{{
        validation?.label
      }}</HelpLabel>
    </h3>
    <ul class="space-y-1.5">
      <li
        v-for="(issue, k) in issues"
        :key="k"
        class="rounded border px-2 py-1.5 text-sm"
        :class="BOX[issue.severity]"
        data-testid="validation-issue"
      >
        <div class="flex items-start gap-2">
          <SeverityIcon :severity="issue.severity" size="md" class="mt-0.5" />
          <span class="min-w-0 flex-1">
            <span class="font-medium">{{ issue.shortMessage }}</span>
            <span class="block text-xs text-gray-600">
              <span v-tooltip="rule?.summary" class="font-mono">{{ issue.rule }}</span>
              · {{ issue.category }} · {{ issue.severity }}
            </span>
          </span>
        </div>
        <details class="mt-1 pl-6 text-xs text-gray-700">
          <summary class="cursor-pointer text-gray-500">more</summary>
          <p class="whitespace-pre-line">{{ issue.message }}</p>
        </details>
      </li>
    </ul>
  </section>
</template>
```

Check the help key format of a concept (`HelpLabel` of the type in `InspectorPanel.vue` gets `typeKey(type)`; find the equivalent for a concept, probably `conceptKey(key)` or the literal `concepts/<key>` the help dialog keys `glossary-details.json` by) and use the helper rather than the literal. The spec wanted the rule number to open its rule text when the glossary cites the rule: look for a lookup from a rule number to the entries that cite it in `glossaryDetails.ts` (`rg -n "rules" frontend/src/report/glossaryDetails.ts | head`); if one exists, make the number a `HelpLabel` with the key of the first citing entry, else keep the tooltip and note the gap in the PR.

- [ ] **Step 4: `ValidationList.vue`**

```vue
<script setup lang="ts">
import { computed, ref } from "vue";

import ElementLink from "@/components/misc/ElementLink.vue";
import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { conceptEntry } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import { groupByRule, SEVERITY_ORDER, type Severity } from "@/report/validation";

/** Every issue of the document, a rule once with the elements it concerns, filtered by severity
 * and by category. */
const props = defineProps<{ index: ReportIndex }>();
const validation = conceptEntry("validation");
const category = conceptEntry("validationCategory");

const shown = ref<Set<Severity>>(new Set(SEVERITY_ORDER));
const chosenCategory = ref<string>("");
const present = computed(() => SEVERITY_ORDER.filter((s) => props.index.issueCounts[s] > 0));
const categories = computed(() => [...new Set(props.index.issues.map((i) => i.category))].sort());
const groups = computed(() =>
  groupByRule(
    props.index.issues.filter(
      (i) =>
        shown.value.has(i.severity) &&
        (chosenCategory.value === "" || i.category === chosenCategory.value),
    ),
  ),
);

function toggle(severity: Severity): void {
  const next = new Set(shown.value);
  if (next.has(severity)) next.delete(severity);
  else next.add(severity);
  shown.value = next;
}
</script>

<template>
  <section class="mb-3" data-testid="validation-list">
    <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
      {{ validation?.label }}
    </h3>
    <p v-if="index.issues.length === 0" class="text-sm text-gray-600" data-testid="no-validation-issues">
      libsbml found no errors or warnings.
    </p>
    <template v-else>
      <div class="mb-2 flex flex-wrap items-center gap-2 text-xs">
        <label v-for="severity in present" :key="severity" class="flex items-center gap-1">
          <input
            type="checkbox"
            :checked="shown.has(severity)"
            :data-testid="`validation-filter-${severity}`"
            @change="toggle(severity)"
          />
          <SeverityIcon :severity="severity" />{{ severity }}
          <span class="text-gray-500 tabular-nums">{{ index.issueCounts[severity] }}</span>
        </label>
        <select
          v-if="categories.length > 1"
          v-model="chosenCategory"
          :aria-label="category?.label"
          class="rounded border border-gray-300 px-1 py-0.5"
          data-testid="validation-filter-category"
        >
          <option value="">all categories</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
      <ul class="divide-y divide-gray-100 text-sm">
        <li v-for="group in groups" :key="group.rule" class="py-1.5" data-testid="validation-group">
          <details>
            <summary class="flex cursor-pointer items-start gap-2">
              <SeverityIcon :severity="group.severity" size="md" class="mt-0.5" />
              <span class="font-mono text-xs text-gray-600">{{ group.rule }}</span>
              <span class="min-w-0 flex-1">{{ group.shortMessage }}</span>
              <span class="text-xs text-gray-500 tabular-nums">{{ group.issues.length }}</span>
            </summary>
            <div class="mt-1 flex flex-wrap gap-1 pl-6">
              <ElementLink v-for="(issue, k) in group.issues" :key="k" :pk="issue.pk" />
            </div>
          </details>
        </li>
      </ul>
    </template>
  </section>
</template>
```

`ElementLink` with a pk only must name the element as every link does; check its props and pass what it needs (`elementLabel(index, pk)` if a label is required). Two issues of one rule on one element give the link twice: dedupe the pks of a group in the `v-for` (`[...new Set(group.issues.map((i) => i.pk))]`).

Use a native `<select>` only if the codebase has no `SelectInput` of its own (`frontend/tests/unit/selectInput.test.ts` says it does): use `components/input/SelectInput.vue` with its props instead, for the same look as the context bar.

- [ ] **Step 5: Mount them in `InspectorPanel.vue`**

Import both, add `const issues = computed(() => index.value?.issuesOf(props.pk) ?? []);` and `const isDocument = computed(() => element.value?.sbmlType === "SBMLDocument");`, and at the start of the first column `div` (before the `Attributes` heading):

```vue
          <ValidationBlock :issues="issues" />
          <ValidationList v-if="isDocument && index" :index="index" />
```

For the document the block shows the issues of the document itself (1090106, read errors at line 0) and the list every issue.

- [ ] **Step 6: Run the tests, the build and the lint**

Run: `cd frontend && npx vitest run && npm run build && npm run lint`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/inspector frontend/tests/unit/inspector.test.ts
git commit -m "The issues of an element and the list of all issues in the inspector (#3)"
```

---

### Task 7: End to end, documentation, screenshots, release note

**Files:**
- Create: `frontend/tests/e2e/validation.spec.ts`
- Modify: `docs/report.md`
- Modify: `frontend/scripts/screenshots.mjs` (if a shot of the validation is added)
- Create: `release-notes/0.11.0.md`
- Retaken: `docs/images/*.png`

**Interfaces:**
- Consumes: every `data-testid` of Tasks 5 and 6; `openExample` of `tests/e2e/helpers.ts`.

- [ ] **Step 1: Write the e2e test**

```ts
import { expect, test } from "@playwright/test";

import { openExample, query } from "./helpers";

const EXAMPLE = "validation (validation.xml)";

test.describe("validation", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, EXAMPLE);
  });

  test("leads from the summary over the list to an element and its issues", async ({ page }) => {
    const summary = page.getByTestId("validation-summary");
    await expect(summary.getByTestId("validation-errors")).toContainText("1");
    await expect(summary.getByTestId("validation-warnings")).toBeVisible();

    await summary.getByTestId("validation-errors").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("SBMLDocument");
    const groups = inspector.getByTestId("validation-list").getByTestId("validation-group");
    await expect(groups.first()).toContainText("10601");

    const compartment = groups.filter({ hasText: "10712" });
    await compartment.locator("summary").click();
    await compartment.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Compartment");
    await expect(inspector.getByTestId("inspector-validation")).toContainText("10712");
    expect(query(page, "pk")).toMatch(/Compartment:cell$/);

    // back returns to the list of the document
    await page.goBack();
    await expect(inspector.getByTestId("validation-list")).toBeVisible();
  });

  test("marks the rows and the types with issues", async ({ page }) => {
    await expect(page.locator('tbody tr[data-pk$="Parameter:k1"]').getByTestId("row-issue")).toBeVisible();
    await expect(page.locator('tbody tr[data-pk$="Species:A"]').getByTestId("row-issue")).toHaveCount(0);
    await expect(page.getByTestId("bar-type-Parameter").getByTestId("severity-warning")).toBeVisible();
  });

  test("a valid model shows no summary", async ({ page }) => {
    await openExample(page, "species (species.xml)");
    await expect(page.getByTestId("validation-summary")).toHaveCount(0);
  });
});
```

Check the example id of `species.xml` in the examples list (`curl -s localhost:1444/api/examples | head -c 600`) and fix it.

- [ ] **Step 2: Run the e2e tests**

Start the backend (`SBML4HUMANS_ALLOW_PRIVATE_URLS=1 uv run uvicorn sbml4humans.api:api --port 1444` from `backend/`, as a tracked background job), then:

Run: `cd frontend && npm run test:e2e -- validation.spec.ts`
Expected: PASS. Then the whole suite: `npm run test:e2e` (the new example joins `examples-walk.spec.ts`; adjust a count there if it pins one).

- [ ] **Step 3: Look at it, pixel by pixel**

With `npm run dev` and the backend running, open the report of `validation`, `random_network` (435 warnings) and `minimal_model_comp` with `chrome-devtools-axi`, at 1400 px and at 360 px, and take screenshots. Check: the chips sit on the line of the context bar and do not push it to two lines at 360 px; the icon in the id cell does not change the row height, also in the windowed table of `random_network`, and the pinned id column of the narrow window still covers the scrolled cells; the dot of the type bar is aligned with the count; the inspector block and the list match the prototype (option C of `.lavish/issue-3-validation.html`). Fix what looks off.

- [ ] **Step 4: Document it**

Add a section "Validation" to `docs/report.md` (one line per paragraph, no em dash): what the chips, the row icon, the dot of the type bar, the inspector block and the list show; that libsbml checks in stages and stops after the first stage with an error; the mapping by position and its limit for comp; that external documents are checked only against those in the report. Link the concept page of the reference (`reference/concepts.md#validation`, check the anchor the generator writes). Add a screenshot of the inspector of the document with the list to `scripts/screenshots.mjs` (follow an existing shot) and reference it from the section.

- [ ] **Step 5: Retake the screenshots**

Run: `cd frontend && npm run screenshots` (backend and dev server running). Review the diff of `docs/images/` and keep only shots that changed for a reason (a shot of a model with issues now shows the chips).

- [ ] **Step 6: The release note**

Check the current version (`rg -n "^version" backend/pyproject.toml`) and the format of an existing note (`ls release-notes | tail -2`), then create `release-notes/0.11.0.md` (the next minor version) in that format with a line: the report shows the validation of libsbml: errors and warnings in the app bar, at the rows and the types, in the inspector of an element and as one list in the inspector of the document (#3).

- [ ] **Step 7: Run every check**

Run:

```bash
cd backend && uv run pytest -q -x && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run python -m sbml4humans.glossary --check && uv run python -m sbml4humans.releasenotes --check
cd .. && uv run --project backend zensical build --clean --strict
cd frontend && npx vitest run && npm run build && npm run lint && npm run build:package
```

Expected: all pass. `releasenotes --check` may fail because the version is not bumped yet; that is the bump PR's job, note it. `build:package` updates `backend/sbml4humans/resources/frontend/`: commit it only if the repository commits that build on feature branches (`git log --oneline -3 -- backend/sbml4humans/resources/frontend`).

- [ ] **Step 8: Commit and open the PR**

```bash
git add frontend/tests/e2e/validation.spec.ts docs/report.md docs/images frontend/scripts/screenshots.mjs release-notes/0.11.0.md
git commit -m "Validation: end to end test, documentation and release note (#3)"
git push -u origin validation
gh-axi pr create --base develop --title "Validation errors and warnings in the report (#3)" --body "Closes #3. ..."
```

The PR body: what the report shows, the resolver and why (an untrusted document could name an absolute path, which the comp validator of libsbml read), the timing of Task 2 Step 6, any gap noted in Task 6 Step 3. No attribution lines.
