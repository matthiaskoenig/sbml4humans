# CLAUDE.md

This file provides guidance when working with code in this repository.

## Project

`sbml4humans` is the web application behind [sbml4humans.de](https://sbml4humans.de): interactive, human readable reports of SBML models. It consists of a FastAPI backend (`backend/`, the `sbml4humans` Python package) and a Vue 3 frontend (`frontend/`). The report itself is not created here: the backend is a thin http layer over `sbmlutils.report.sbmlinfo.SBMLDocumentInfo` of [sbmlutils](https://github.com/matthiaskoenig/sbmlutils), and the frontend renders the dictionary it returns. Until sbmlutils 0.10.0 the application lived in the sbmlutils repository, it was moved here with its history so that sbmlutils stays a library.

The backend requires python >= 3.14 and is packaged with hatchling (version read from `backend/sbml4humans/__init__.py`). Runtime dependencies are `sbmlutils`, `fastapi`, `uvicorn`, `python-multipart` (uploads) and `httpx` (downloading models from urls). The frontend is a Vue CLI 4 project (webpack 4) with TypeScript, Vuex, Vue Router and PrimeVue.

## Commands

```bash
# the sbmlutils checkout must be next to this repository, see [tool.uv.sources]
git clone https://github.com/matthiaskoenig/sbmlutils.git ../sbmlutils

# backend, from backend/ (uv based)
uv sync                                          # venv, dependencies of uv.lock, editable ../../sbmlutils
uv run uvicorn sbml4humans.api:api --reload --port 1444   # add --reload-dir ../../sbmlutils/src to reload on checkout changes
uv run pytest                                    # all tests
uv run pytest tests/test_api.py::test_examples   # single test
uv run ruff check . && uv run ruff format --check .
uv run ty check                                  # type check, warnings are errors

# latest local sbmlutils: code changes are live (editable install), only its
# dependencies are locked, so re-sync after updating the checkout and commit uv.lock
git -C ../sbmlutils pull && uv sync

# frontend, from frontend/ (node 14, see .nvmrc)
nvm use
npm ci           # from package-lock.json, npm install updates the lock
npm run serve      # http://localhost:3456, api on http://localhost:1444 (.env.development)
npm run build      # production build into dist/
npm run lint
npm run test:unit
npm run test:e2e

# both services in containers, from the repository root
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up   # frontend :8083, api :1444
```

`main` is the only branch. The CI (`.github/workflows/`) checks out sbmlutils next to the repository, runs `pytest` (`ci.yml`), `ruff` and `ty` on every push; a tag runs the tests and then creates the GitHub release from `release-notes/<tag>.md`.

Releases: the version of sbml4humans is the version of the backend package, `frontend/package.json` follows it. Write `release-notes/<version>.md` first, then from `backend/` run `uv run bump-my-version bump [major|minor|patch]`, which updates both files, commits and tags; `git push origin main --tags` triggers the release workflow. Never edit the version by hand.

## Architecture

**`backend/sbml4humans/api.py` - the http api.** A FastAPI app `api` with CORS open to every origin. Endpoints: `GET /api/examples` (metadata of the examples), `GET /api/examples/{id}` (report of an example), `POST /api/file` (upload), `GET /api/url` (download and report), `POST /api/content` (raw SBML in the body) and `GET /api/annotation_resource` (resolves an annotation resource via pymetadata). The lifespan handler loads the examples on startup. Report creation is synchronous and CPU bound, the async endpoint delegates to `run_in_threadpool`. `main()` runs uvicorn for `python -m sbml4humans.api`.

**Error contract.** The frontend expects every response with status 200. Every failure, including validation errors, is answered by `error_response` with status 200 and a body `{"errors": [message, traceback], "warnings": [], "info": {query parameters}}`. The tests run the `TestClient` with `raise_server_exceptions=False` to test this contract, keep it that way.

**`report.py` - the report.** `report_for_path`/`report_for_bytes` accept SBML (plain or gzipped) and COMBINE archives (omex, the master SBML entry of the manifest is reported) and return the dictionary of `SBMLDocumentInfo`. The frontend renders this dictionary as is, changes to its structure happen in sbmlutils.

**`examples.py` - the examples.** `load_examples` collects the example models of `sbml4humans/resources/` (`API_EXAMPLES_MODEL`, `API_EXAMPLES_OMEX`, the first 49 curated BioModels in `BIOMODELS_CURATED_PATH`) into `ExampleMetaData` (pydantic). The resources were copied from sbmlutils and ship in the package, the api does not import `sbmlutils.resources`.

**`frontend/src`.** `main.ts` creates the app; `router/index.ts` the routes; `store/index.ts` the single Vuex store, which fetches the report from the api (`VUE_APP_APIURL`) and holds the current report and the search state. `components/layout/` is the page frame (navbar, upload forms, about), `components/sbml/` one component per SBML element type of the report, `components/tables/` the tables and `components/sbmlmisc/` the shared pieces (math, annotations, notes). `helpers/` holds the report initialization and the lookups, `data/` the static tables of the SBML element types, their colors and the Font Awesome icons.

**Deployment.** `Dockerfile` (backend) clones the sbmlutils `develop` branch into `/opt/sbmlutils` and installs it editable, `frontend/Dockerfile-develop` and `Dockerfile-production` build the frontend on node 14, `nginx/` is the proxy of sbml4humans.de and `deploy.md`/`deploy.sh` describe the server. The production compose file is `docker-compose-production.yml`.

## Conventions

- Type checking is done with [ty](https://docs.astral.sh/ty/), `error-on-warning = true` means the backend must stay at zero diagnostics. Suppress a diagnostic with a rule-specific `# ty: ignore[rule-name]`, never a blanket `# type: ignore`. Ruff runs with the rule set listed in `backend/pyproject.toml` (google style docstrings, isort, pyupgrade, bugbear, lazy `%s` logging), every module, class and function is annotated and has a docstring.
- The backend follows the conventions of sbmlutils (see its `CLAUDE.md`): it logs through `logging.getLogger(__name__)` and never configures logging, and libsbml objects are accessed through their getters.
- `uv.lock` is committed and the CI installs from it. The lock also pins the dependencies of the sbmlutils checkout, so after a `git pull` of `../sbmlutils` that changes its `pyproject.toml`, `uv sync` rewrites `uv.lock` and the diff belongs into the commit.
- `uv sync` reinstalls `antimony` on every run: the linux wheel of antimony 3.1.3 is tagged `py3-none` in its filename but `cp313` in its metadata. This is harmless and cannot be fixed here, sbmlutils excludes 3.2.0 on windows and uv resolves one version for all platforms.
- The frontend needs node 14 (`frontend/.nvmrc`): Vue CLI 4 is webpack 4, which cannot parse modern syntax such as optional chaining in dependencies, and `node-sass` 4 does not build on newer node. `package-lock.json` is committed (lockfile version 1, written by the npm 6 of node 14) and the containers install with `npm ci`; commit the lock with every dependency change. A release of a dependency that breaks the build is capped in `package.json` (`vue-router` `<4.6.4`), verify with `npm run build` after changing ranges.
- Markdown carries no hard line wraps: a paragraph, a list item or a table row is a single line. Never use the em dash, use a plain dash.
- Release notes go in `release-notes/<version>.md` before the version is bumped, the file is the body of the GitHub release.
