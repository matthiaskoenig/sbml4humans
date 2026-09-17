# CLAUDE.md

This file provides guidance when working with code in this repository.

## Project

`sbml4humans` is the web application behind [sbml4humans.de](https://sbml4humans.de): interactive, human readable reports of SBML models. It consists of a FastAPI backend (`backend/`, the `sbml4humans` Python package) and a Vue 3 frontend (`frontend/`). The backend creates the report of a document (`sbmlinfo.SBMLDocumentInfo`) and serves it over http as the typed `ReportResponse`. The Vue frontend renders the typed report: one table per element type, a search, and an inspector that follows the link graph. The report is self-contained: the repository has no dependency on any SBML model building library, do not add one.

The backend requires python >= 3.14 and is packaged with hatchling (version read from `backend/sbml4humans/__init__.py`). Runtime dependencies are `python-libsbml` (reading the models), `lxml` (the xslt rendering of the math), `pint` (units), `numpy`, `pymetadata` (COMBINE archives, annotation resolution), `pydantic` (the report data model), `fastapi`, `uvicorn`, `python-multipart` (uploads) and `httpx` (downloading models from urls). The frontend is a Vite 8 project (node 24) with Vue 3.5, TypeScript, Pinia, Vue Router 5 and PrimeVue 4 in unstyled mode with Tailwind CSS 4.

## Commands

```bash
# backend, from backend/ (uv based)
uv sync                                          # venv with the dependencies of uv.lock, editable package
uv run uvicorn sbml4humans.api:api --reload --port 1444
uv run pytest                                    # all tests
uv run pytest tests/test_api.py::test_examples   # single test
uv run ruff check . && uv run ruff format --check .
uv run ty check                                  # type check, warnings are errors
uv run python -m sbml4humans.schema              # regenerate the JSON schema after a model change

# dependency changes go through uv and are committed with uv.lock
uv add <package>

# frontend, from frontend/ (node 24, see .nvmrc)
nvm use
npm ci           # from package-lock.json, npm install updates the lock
npm run dev        # http://localhost:3456, api on http://localhost:1444 (.env.development)
npm run build      # type check and production build into dist/
npm run lint
npm run typecheck
npm run test:unit
npm run test:e2e   # backend on port 1444 required
npm run types      # regenerate src/types/report.ts after a schema change, the CI diffs it
npm run fixtures   # regenerate tests/fixtures/*.json after a model change, by hand

# both services in containers, from the repository root
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up   # frontend :8083, api :1444
```

`develop` takes every change through a pull request; direct pushes are rejected by the rulesets in `.github/rulesets/` (applied with `.github/rulesets/apply.sh`), which require the `test`, `schema`, `frontend`, `e2e`, `ruff` and `ty` checks and allow only squash or rebase merges. `main` only tracks the latest release and is fast-forwarded by the `sync-main` job of `ci.yml`, never by hand; tags cannot be moved or deleted. The CI (`.github/workflows/`) runs `pytest` (`ci.yml`), `ruff` and `ty` on every pull request and push to `develop` and `main`, and in `ci.yml` also the frontend lint, type check, unit tests and build (`frontend`) and the Playwright end to end tests (`e2e`); the release job needs `test`, `schema`, `frontend` and `e2e` and, on a tag, creates the GitHub release from `release-notes/<tag>.md`.

Releases: the version of sbml4humans is the version of the backend package, `frontend/package.json` follows it. Write `release-notes/<version>.md` first, then from `backend/` run `uv run bump-my-version bump [major|minor|patch]`, which updates both files and commits without tagging (`tag = false`, a squash merge would rewrite the commit). The bump goes through a pull request like every change, and the tag is created on `develop` after the merge; pushing it triggers the release workflow. Steps in the Releases section of `README.md`. Never edit the version by hand.

## Architecture

**`backend/sbml4humans/api.py` - the http api.** A FastAPI app `api` with CORS open to every origin. Endpoints: `GET /api/examples` (metadata of the examples), `GET /api/examples/{id}` (report of an example), `POST /api/file` (upload), `GET /api/url` (download and report), `POST /api/content` (raw SBML in the body) and `GET /api/annotation_resource` (resolves an annotation resource via pymetadata). The lifespan handler loads the examples on startup. Report creation is synchronous and CPU bound, the async endpoint delegates to `run_in_threadpool`.

**`model.py`, `sbmlinfo.py`, `links.py` - the report.** `model.py` is the pydantic data model: one class per SBML object with the attributes of the specification (`Species`, `Reaction` with `SpeciesReference` and `KineticLaw`, the comp and fbc objects), `Model` with the SBML lists (`list_of_species`, ...), `Report{document, models, external_model_definitions, link_graph}`. Python is snake_case, JSON camelCase (`model_dump(mode="json", by_alias=True)`). `sbmlinfo.SBMLDocumentInfo` walks the libsbml document and builds the objects, math as `Math{latex, formula}` (`mathml.py`) and units as latex (`units.py`), and records the symbols of every math. `links.build_link_graph` turns the report into `LinkGraph{nodes, edges}`: every SBase is a node with `pk = "<model id>/<type>:<id>"`, every reference (compartment, reactant, variable, units, math symbols, modelRef, port, flux bounds, ...) an `Edge{source, target, kind}` from the referencing to the referenced object; unresolvable references are logged, never edges. `schema.py` writes the JSON schema of `ReportResponse` to `frontend/src/schema/report.schema.json`, run it after every model change (the CI diffs it).

**Error contract.** The frontend expects every response with status 200. Every failure, including validation errors, is answered by `error_response` with status 200 and a body `{"errors": [message, traceback], "warnings": [], "info": {query parameters}}`. The tests run the `TestClient` with `raise_server_exceptions=False` to test this contract, keep it that way.

**`report.py` - the archive layer.** `report_for_path`/`report_for_bytes` accept SBML (plain or gzipped) and COMBINE archives (omex, one report per SBML entry of the manifest) and wrap the `Report` of every SBML entry with the manifest into a `ReportResponse`.

**`examples.py` - the examples.** `load_examples` collects the example models of `sbml4humans/resources/` (`API_EXAMPLES_MODEL`, `API_EXAMPLES_OMEX`, the first 49 curated BioModels in `BIOMODELS_CURATED_PATH`) into `ExampleMetaData` (pydantic). The resources ship in the package.

**`frontend/src`.** `api/` is the fetch client with the error contract (`ApiError`) and the report types, generated into `types/report.ts` by `npm run types`. `stores/` are the Pinia stores of the report and the examples. `report/` holds `ReportIndex` (every element by pk, the edges of the link graph), `search` and `query` (the search and the view state of the report page kept in the route query) and `columns/` (the table columns per element type). `pages/` are the routed pages: home (upload, url, paste), examples, report. `components/` is split into `layout/` (app bar, split panes, states), `input/` (the upload forms), `report/` (context bar, type rail, search, element tables), `inspector/` (attributes per type, links, annotations), and `misc/` (math, units, links, notes, xml, shared across the other groups). `data/` holds the order, labels, colours and icons of the SBML element types and the edge kinds.

**Deployment.** `Dockerfile` (backend) installs the package editable into a `python:3.14-slim` image, `frontend/Dockerfile-develop` and `Dockerfile-production` build the frontend on node 24, `nginx/` is the proxy of sbml4humans.de and `deploy.md`/`deploy.sh` describe the server. The production compose file is `docker-compose-production.yml`.

## Conventions

- Type checking is done with [ty](https://docs.astral.sh/ty/), `error-on-warning = true` means the backend must stay at zero diagnostics. Suppress a diagnostic with a rule-specific `# ty: ignore[rule-name]`, never a blanket `# type: ignore`. Ruff runs with the rule set listed in `backend/pyproject.toml` (google style docstrings, isort, pyupgrade, bugbear, lazy `%s` logging), every module, class and function is annotated and has a docstring.
- The backend logs through `logging.getLogger(__name__)` and never configures logging (uvicorn does). libsbml has no type stubs and builds its objects through SWIG, so annotate libsbml objects explicitly and use the getters (`getId()`) rather than the attributes SWIG synthesizes.
- `uv.lock` is committed and the CI installs from it, every dependency change is committed with the updated lock.
- The frontend needs node 24 (`frontend/.nvmrc`). `package-lock.json` is committed and the containers install with `npm ci`; commit the lock with every dependency change. TypeScript stays at `~6.0.3` while `typescript-eslint` supports TypeScript below 6.1 only; PrimeVue stays at `^4.5.5` (MIT, PrimeVue 5 is commercial). Components resolve cross references through `ReportIndex` and never build a pk from an id. Every element an end to end test uses carries a `data-testid`.
- Markdown carries no hard line wraps: a paragraph, a list item or a table row is a single line. Never use the em dash, use a plain dash.
- Release notes go in `release-notes/<version>.md` before the version is bumped, the file is the body of the GitHub release.
