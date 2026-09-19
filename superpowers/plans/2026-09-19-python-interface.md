# Python Interface Implementation Plan

**Goal:** `sbml4humans.show(path)` and the command `sbml4humans PATH` open the report of a local file in the browser, served by a local server which ships with the wheel.

**Spec:** `superpowers/specs/2026-09-19-python-interface-design.md`

**Branch:** `python-interface` on top of `external-models` (#36), one pull request which closes #33.

## Global Constraints

As in `2026-09-19-external-model-definitions.md`: test first, all checks before every commit, no em dash, no hard line wraps, commit messages of one sentence without `Co-Authored-By`.

---

### Task 1: the local app

- [x] `tests/test_local.py`, then `sbml4humans/local.py`: `ReportStore`, `LocalApp` (routing, host and origin check, static files with fallback), the local endpoints with the secret and the error contract. `api.py` shares its error contract as `add_error_contract(app)`.

### Task 2: the server process

- [x] `serve()` with the state file and the idle watcher, `python -m sbml4humans.local`. `platformdirs` becomes a dependency (`uv add`).

### Task 3: `show()`, `stop()` and the command

- [x] `tests/test_show.py`, then `sbml4humans/show.py`, the export in `__init__.py`, `cli.py` and the console script.

### Task 4: the frontend

- [x] Unit tests, then the client (`getLocal`, `pingLocal`), the store (`loadLocal`), the page (`local` in the route, the ping), `view.ts` keeps `local`.
- [x] `.env.package`, `npm run build:package`, `VITE_ANALYTICS`, the git ignore of the build.
- [x] End to end test of `/report?local=`.

### Task 5: packaging and CI

- [x] `artifacts` of hatch, the `package` job, the `publish` job.
- [x] The real thing by hand: build, install the wheel into a fresh environment, `sbml4humans` on a comp model, look at the page in the browser.

### Task 6: documentation and the pull request

- [x] `docs/python.md` and the navigation, `docs/inputs.md`, `docs/development.md` (the build of the package, PyPI), `README.md`, `CLAUDE.md`.
- [x] All checks, push, pull request which closes #33.
