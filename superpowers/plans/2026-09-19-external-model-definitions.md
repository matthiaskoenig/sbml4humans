# External Model Definitions Implementation Plan

**Goal:** the references of a comp model end at the element they name where the submodel instantiates an external model definition whose document is an entry of the archive or a file next to a trusted single file.

**Spec:** `superpowers/specs/2026-09-19-external-model-definitions-design.md`

**Branch:** `external-models` from `develop`, one pull request which closes #36.

## Global Constraints

- Test first: every task writes the failing test, sees it fail, then implements.
- Before every commit: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run pytest`, and for frontend changes `cd frontend && npm run lint && npm run typecheck && npm run test:unit`.
- No em dash, markdown without hard line wraps, every module, class and function annotated and with a docstring, libsbml through its getters.
- Commit messages: one descriptive sentence, no conventional prefix, no `Co-Authored-By`.

---

### Task 1: the data model

- [x] `model.py`: `ResolutionStatus`, `ExternalModelResolution`, `ExternalModelDefinition.resolution` (default `notFound`), `Edge.target_entry`.
- [x] `tests/test_model.py`: the JSON of both in camelCase, `targetEntry` is `null` by default.
- [x] `uv run python -m sbml4humans.schema`, `npm run types`.

### Task 2: `external.py`

- [x] `tests/test_external.py`: `resolve_source` and `normalize_location` (relative, nested, root, scheme, escape, percent encoding).
- [x] `resolve_source`, `normalize_location`.
- [x] Tests of `ExternalModels` on small comp documents written in the test: every status, a chain over two documents, a circle, md5 match and mismatch.
- [x] `ExternalModels.resolve`, `resolve_all`.

### Task 3: the graph across entries

- [x] `tests/test_links.py`: a replaced element, a replaced by, a deletion and a port which end in another entry carry `target_entry`; a chain which enters a third entry; the edge of the external model definition to its model; every edge target is a node of the graph its `target_entry` names.
- [x] `links.py`: `EntryIndex`, `Target`, `ModelIndex.entry`, `_submodel_index` through `ExternalModels`, the resolution functions return `Target`, `build_link_graphs` for a set of reports, `build_link_graph` stays the graph of one report.

### Task 4: the two phases and the trusted directory

- [x] `tests/test_report.py`: an archive links across its entries; a trusted single file gains its sibling entries (transitively), is named after its file, and an untrusted one gains none; `../` and absolute sources are refused.
- [x] `sbmlinfo.py`: `build_report()`; `report.py`: `link_reports`, `report_for_path(path, trusted)`, the sibling worklist; `api.py`: the examples are read trusted.
- [x] `tests/test_examples.py::test_comp_references_reach_elements`, the measure of the issue.

### Task 5: the glossary

- [x] `glossary/packages.toml` and `glossary/report.toml`: the resolution, its fields, its statuses, the link across entries.
- [x] `uv run python -m sbml4humans.glossary`, `--check` is green.

### Task 6: the frontend

- [x] `npm run fixtures` and a fixture of `CompModels`.
- [x] Unit tests, then `ReportIndex.location`, incoming edges across entries registered by the store, a lookup of a node of another entry.
- [x] The links of the inspector and the reference cells show and follow an edge with `targetEntry`.
- [x] The inspector of the external model definition shows the resolution.
- [x] End to end test: from the replaced element of `omex_comp.xml` to the element of `omex_minimal.xml` and back. Every element it uses carries a `data-testid`.
- [x] Look at the result in the browser, at desktop and at phone width, and fix what looks off.

### Task 7: documentation and the pull request

- [x] `docs/report.md` and `docs/inputs.md`: what is resolved, what is not, and why nothing is fetched. `CLAUDE.md`: the architecture paragraph of the report.
- [x] Retake a screenshot which became wrong.
- [x] All checks, the docs build, push, pull request which closes #36.
