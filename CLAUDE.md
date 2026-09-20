# CLAUDE.md

This file provides guidance when working with code in this repository.

## Project

`sbml4humans` is the web application behind [sbml4humans.de](https://sbml4humans.de): interactive, human readable reports of SBML models. It consists of a FastAPI backend (`backend/`, the `sbml4humans` Python package) and a Vue 3 frontend (`frontend/`). The backend creates the report of a document (`sbmlinfo.SBMLDocumentInfo`) and serves it over http as the typed `ReportResponse`. The Vue frontend renders the typed report: one table per element type, a search, and an inspector that follows the link graph. The package is also the python interface: `sbml4humans.show(path)` and the command `sbml4humans` open the report of a local file in the browser, served by a local server which ships the built frontend. The report is self-contained: the repository has no dependency on any SBML model building library, do not add one.

## Commands

```bash
# backend, from backend/ (uv based)
uv run uvicorn sbml4humans.api:api --reload --port 1444
uv run ruff check . && uv run ruff format --check .
uv run ty check                                  # type check, warnings are errors
uv run python -m sbml4humans.schema              # regenerate the JSON schema after a model change

# frontend, from frontend/ (node 24, see .nvmrc)
npm run dev          # http://localhost:3456, api on http://localhost:1444 (.env.development)
npm run build        # type check and production build into dist/
npm run build:package  # the build the python package ships, into backend/sbml4humans/resources/frontend/
npm run test:e2e     # backend on port 1444 required
npm run types        # regenerate src/types/report.ts after a schema change, the CI diffs it
npm run fixtures     # regenerate tests/fixtures/*.json after a model change, by hand
npm run screenshots  # retake docs/images/*.png, needs the backend and a dev server, see scripts/screenshots.mjs

# the documentation, from backend/ and from the repository root
uv run python -m sbml4humans.glossary            # regenerate glossary.json and docs/reference/
uv run python -m sbml4humans.glossary --check    # fails when they are stale or incomplete
uv run python -m sbml4humans.releasenotes        # regenerate docs/release-notes.md from release-notes/
uv run python -m sbml4humans.releasenotes --check  # fails when it is stale or the version has no notes
uv run --project backend zensical serve          # live preview of the site
uv run --project backend zensical build --clean --strict  # build into site/, a broken link fails

# both services in containers, from the repository root
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up   # frontend :8083, api :1444
```

`develop` takes every change through a pull request; direct pushes are rejected by the rulesets in `.github/rulesets/` (applied with `.github/rulesets/apply.sh`), which require the `test`, `schema`, `frontend`, `e2e`, `ruff`, `ty` and `docs` checks and allow only squash or rebase merges. `main` only tracks the latest release and is fast-forwarded by the `sync-main` job of `ci-cd.yml`, never by hand; tags cannot be moved or deleted.

Releases: the version of sbml4humans is the version of the backend package, `frontend/package.json` and its lock follow it. Write `release-notes/<version>.md` first, then from `backend/` run `uv run bump-my-version bump [major|minor|patch]`, which updates all of them and commits without tagging (`tag = false`, a squash merge would rewrite the commit). The bump goes through a pull request like every change, and the tag is created on `develop` after the merge; pushing it triggers the release workflow. Steps in the Releases section of `docs/development.md`. Never edit the version by hand.

## Architecture

The architecture of the backend is described in `backend/CLAUDE.md`, of the frontend in `frontend/CLAUDE.md` and of the glossary in `glossary/CLAUDE.md`; each is loaded with the first file read below its directory. Read `glossary/CLAUDE.md` also before a change of `backend/sbml4humans/glossary.py`, of `glossaryrules.py`, of the report model or of a label in the frontend.

**Error contract.** The frontend expects every response with status 200. Every failure, including validation errors, is answered by `error_response` with status 200 and a body `{"errors": [message, traceback], "warnings": [], "info": {query parameters}}`. The tests run the `TestClient` with `raise_server_exceptions=False` to test this contract, keep it that way.

**The glossary.** `glossary/*.toml` in the repository root is the single source of every explanation and of every name: nothing is explained or named anywhere else, the frontend states no names of its own (the only words it owns are the chrome of the help dialog in `components/help/words.ts` and in the components themselves), and nothing of a validation rule is ever written by hand (`glossaryrules.resolve_rule` makes a rule text). Run `uv run python -m sbml4humans.glossary` after a change of the glossary or of the report model and commit all three outputs (`frontend/src/data/glossary.json`, `frontend/src/data/glossary-details.json`, `docs/reference/*.md`). The entry format and what `--check` enforces are in `glossary/CLAUDE.md`.

**The documentation site.** The sources are `docs/` (`index.md`, `sbml.md`, `inputs.md`, `report.md`, the generated `reference/`, `references.md`, `development.md`), the configuration and the navigation are `zensical.toml`, and the site is built from the repository root with `uv run --project backend zensical build --clean --strict` into the git ignored `site/`. `docs/release-notes.md` is generated from `release-notes/*.md` by `sbml4humans.releasenotes`, the versions newest first, and the version bump runs the generator as a hook. The `docs` job of `.github/workflows/docs.yml` runs the glossary check, the release notes check and the build on every pull request, and its `deploy` job publishes the site to GitHub Pages from `develop` to <https://matthiaskoenig.github.io/sbml4humans/>. The screenshots of `docs/images/` are taken by `frontend/scripts/screenshots.mjs` (`npm run screenshots`) against a running backend and dev server and are committed; retake them when a change of the user interface makes one of them wrong.

**Deployment.** `Dockerfile` (backend) installs the package editable into a `python:3.14-slim` image, `frontend/Dockerfile-develop` and `Dockerfile-production` build the frontend on node 24, `nginx/` is the proxy of sbml4humans.de and `deploy.md`/`deploy.sh` describe the server; they stay out of `docs/`, the documentation site does not carry the server. The production compose file is `docker-compose-production.yml`.

## Conventions

- Type checking is done with [ty](https://docs.astral.sh/ty/), `error-on-warning = true` means the backend must stay at zero diagnostics. Suppress a diagnostic with a rule-specific `# ty: ignore[rule-name]`, never a blanket `# type: ignore`. Ruff runs with the rule set listed in `backend/pyproject.toml` (google style docstrings, isort, pyupgrade, bugbear, lazy `%s` logging), every module, class and function is annotated and has a docstring.
- The backend logs through `logging.getLogger(__name__)` and never configures logging (uvicorn does). libsbml has no type stubs and builds its objects through SWIG, so annotate libsbml objects explicitly and use the getters (`getId()`) rather than the attributes SWIG synthesizes.
- `report_for_path(path, trusted=True)` also reads the files next to an SBML file. It is set for the shipped examples and for the path the local server of `show` is given, and never for a path which holds the content of a request (upload, url, pasted content).
- Do not name a module `show`, it would shadow the function `sbml4humans.show`.
- `uv.lock` is committed and the CI installs from it, every dependency change is committed with the updated lock.
- The frontend needs node 24 (`frontend/.nvmrc`). `package-lock.json` is committed and the containers install with `npm ci`; commit the lock with every dependency change. TypeScript stays at `~6.0.3` while `typescript-eslint` supports TypeScript below 6.1 only. PrimeVue and PrimeIcons are not used: from PrimeVue 5 and PrimeIcons 8 on they are commercial (PrimeUI license); new dependencies have to be MIT, ISC or a comparable permissive license. Components resolve cross references through `ReportIndex` and never build a pk from an id. Every element an end to end test uses carries a `data-testid`.
- Markdown carries no hard line wraps: a paragraph, a list item or a table row is a single line. Never use the em dash, use a plain dash.
- Release notes go in `release-notes/<version>.md` before the version is bumped, the file is the body of the GitHub release and a section of `docs/release-notes.md`, which is generated and never edited by hand.
