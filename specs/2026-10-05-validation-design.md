# Validation errors and warnings in the report (#3)

Design approved on 2026-10-05. Prototype of the user interface: `.lavish/issue-3-validation.html` (git ignored), option C (the list of all issues in the inspector of the document), unit consistency checks on and grouped by rule, a severity icon in the id cell of a row.

## Goal

The report shows the validation of libsbml: every error and warning of a document, attached to the element it concerns, as hints in the tables and in the inspector, and as one list of all issues. The reader sees at a glance whether a model is valid, which elements have issues and what they are.

## Today

- No consistency check runs. `sbml.read_sbml` logs the read errors of libsbml (`log_sbml_error`) and drops them.
- The only error which reaches the user is the read error log of a document without a model, raised as `ValueError` by `report._Entry` and answered by `api.error_response`. The `warnings` of the error envelope are always empty.
- `ReportResponse`, `ReportEntry` and `Report` have no field for errors or warnings, and no element records its line in the file.
- `glossaryrules.resolve_rule` turns a rule number into its text, used only for the rules the glossary cites, shown in the help dialog (`HelpRules.vue`).
- Of the 31 shipped examples, 19 have no issue, 10 only warnings (mostly unit consistency, 99505 to 99508, up to 435 for `random_network`), `comp_deletion` and `minimal_model_comp` have errors (1090101, 1020615). `checkConsistency()` takes at most 0.02 s on them.

## Scope

In: the read errors and the default consistency checks of libsbml (`checkConsistency()` with the categories libsbml enables by default, unit consistency included) for every report entry, the main document and every external model definition document; their mapping to the elements; the hints in the app bar, the type bar, the tables and the inspector; the list of all issues in the inspector of the document.

Out: checks which libsbml does not enable by default, a choice of the categories by the reader, a validation of its own beyond libsbml, a change of the error contract (a document without a model is still answered by `error_response`).

## 1. Backend

**Validation.** `_Entry` validates the document after it is read: the issues are the read errors of libsbml followed by those of `doc.checkConsistency()`. A new module `validation.py` holds the validation and the mapping, so `report.py` and `sbmlinfo.py` only call it.

- The severity of libsbml becomes `error` (`LIBSBML_SEV_ERROR`, `LIBSBML_SEV_FATAL`), `warning` or `info`.
- `category` is `getCategoryAsString()`, `short_message` `getShortMessage()`, `message` `getMessage()` stripped; nothing of an issue is written by hand.
- An issue which libsbml reports twice (same rule, line, column and message) is kept once.

**Mapping an issue to an element.** libsbml reports only the line (and column) of an issue, no element.

- While the report is built, every `SBase` of the report records the line and column at which its element starts (`getLine()`, `getColumn()`) in the mapping, not in the report model.
- An issue goes to the element whose start is the closest at or before the position of the issue, comparing line and then column; of elements starting at the same position the innermost one wins.
- An issue at line 0, before the first element, or of a document whose elements have no lines goes to the `SBMLDocument`. Every issue thus has a pk.
- For a document which uses comp, libsbml instantiates the submodels for its checks and its line numbers are unreliable; libsbml says so with the warning 1090106, which stays in the list so the reader knows the mapping can be off.

**Untrusted documents.** The comp validator resolves the `source` of an external model definition through the global `SBMLResolverRegistry` of libsbml, relative to the location of the document. For a report which is not `trusted` (upload, url, pasted content) validation must never read a file or a url which the content names.

- The implementation first establishes what libsbml resolves (an absolute path, a relative path, an `http` url) with a test per case.
- If resolution can be confined for an untrusted report without touching the registry of other concurrent reports, comp validation stays on. Otherwise an untrusted report validates with the comp consistency category off (`setConsistencyChecks`), and the trusted reports keep it.
- The tests show that an untrusted document whose external model definition names an existing absolute path or a url is validated without that file being read or that url requested.

**Model** (`model.py`, then the JSON schema, `npm run types`, `npm run fixtures`):

- `ValidationIssue`: `rule: int`, `severity: Severity`, `category: str`, `short_message: str`, `message: str`, `line: int`, `column: int`, `pk: str`
- `Severity`: `Literal["error", "warning", "info"]`
- `Report.validation: list[ValidationIssue]`, in the order of libsbml.

**Glossary.** `ValidationIssue`, its fields and `Severity` get entries in `glossary/report.toml`, labelled in plain words (they are what the report adds), so the frontend takes every name of the validation from the glossary. Regenerate and commit `glossary.json`, `glossary-details.json` and `docs/reference/`.

## 2. Frontend

**ReportIndex.** `issuesOf(pk)` (the issues of an element, errors first), `worstSeverity(pk)`, the counts of the document per severity and `typesWithIssues` (the worst severity per type). Components take the issues only from the index.

**App bar.** Next to the name and the level of the document a chip for the errors (red) and one for the warnings (amber), each with its count, shown only when there are any; info issues get no chip. A click on a chip selects the `SBMLDocument`, whose inspector holds the list. `data-testid="validation-summary"`.

**Type bar.** A red or amber dot after the count of a type which has issues, with the worst severity of its elements.

**Tables.** `ElementTable` shows a severity icon before the id of a row with errors or warnings (red for errors, amber for warnings, none for info only). Hovering over the icon shows the short messages of the row with their rule numbers; a click on the row selects it as before. `data-testid="row-issue"`.

**Inspector of an element.** A block "Validation" at the top, above the attributes, when the element has issues: per issue the severity icon, the short message, the rule number, the category and the severity, the full message behind "more". The rule number opens its rule text in the help dialog when the glossary cites the rule, else it is plain text. `data-testid="inspector-validation"`.

**Inspector of the document.** The list of all issues of the document, below its own issues:

- grouped by rule, errors first, then warnings, then info; a group shows its severity, the rule number, the short message and the number of its issues;
- a group expands to the elements of its issues, each a link which selects the element; the selection is part of the route (`report/view.ts`), so the back of the browser returns to the list;
- filters by severity and by category above the list;
- a report without issues states that libsbml found none.

Unit consistency issues stay in the list, the grouping keeps each of their rules to one line. `data-testid="validation-list"`.

**Words.** Every label comes from the glossary; the chrome (`more`, the filter of all categories, the message without issues) is owned by the components, as for the help dialog.

## 3. Testing

- Backend (`pytest`): the issues of `minimal_model_comp` (errors 1020615 and 1090101 on their elements, the 1090106 warning), of `comp_deletion` and of `reaction` (unit warnings on the compartment and the species); a valid example has no issues; the mapping with a synthetic document (an issue on the line of a nested element, two elements on one line, line 0); the untrusted resolution cases; duplicate issues are kept once.
- Frontend: unit tests of the `ReportIndex` lookups; an e2e test which opens `minimal_model_comp`, checks the chips, clicks one, finds the list in the inspector of the document, expands a group, follows a link to the element and finds its validation block and the icon of its row.
- Lint, `ty`, the glossary check, the schema check and the docs build pass.

## 4. Documentation and release

- `docs/report.md` describes the validation: the chips, the markers, the inspector block, the list, the mapping by line and its limits for comp.
- The screenshots of `docs/images/` which show the app bar or a row with issues are retaken (`npm run screenshots`).
- A release note in `release-notes/<next version>.md`.
