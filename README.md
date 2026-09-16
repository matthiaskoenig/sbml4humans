# SBML4Humans

[SBML4Humans](https://sbml4humans.de) renders [SBML](https://sbml.org) models as interactive, human readable reports: a Vue frontend on top of a FastAPI backend which serves the report of [sbmlutils](https://github.com/matthiaskoenig/sbmlutils).

Until sbmlutils 0.10.0 the application lived in the sbmlutils repository. It was moved here with its history so that sbmlutils stays a library and the web application can be released independently.

## Repository layout

| path | content |
| --- | --- |
| `frontend/` | the Vue 3 application (TypeScript, Vuex, Vue Router, PrimeVue) |
| `backend/` | the `sbml4humans` Python package: a FastAPI api, a thin http layer over `sbmlutils.report.sbmlinfo.SBMLDocumentInfo` |
| `nginx/` | the proxy configuration of sbml4humans.de |
| `Dockerfile`, `docker-compose-*.yml` | the containers of the backend, the frontend and the proxy |
| `deploy.md`, `deploy.sh`, `docker-purge.sh` | deployment of the server |

## Development

Clone this repository and the [sbmlutils](https://github.com/matthiaskoenig/sbmlutils) repository next to each other. The backend develops against the sbmlutils checkout, not against the release on PyPI (see below), so the layout must be:

```bash
git clone https://github.com/matthiaskoenig/sbml4humans.git
git clone https://github.com/matthiaskoenig/sbmlutils.git
cd sbml4humans
```

### Frontend and backend with docker compose

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

The backend container installs sbmlutils from its latest `develop` branch on GitHub, the local checkout is not used. The frontend answers on <http://localhost:8083>, the api on <http://localhost:1444>.

### Backend

The backend is the `sbml4humans` Python package in `backend/`, it requires Python 3.14 and [uv](https://docs.astral.sh/uv/). `[tool.uv.sources]` in `backend/pyproject.toml` points uv at the `../sbmlutils` checkout next to this repository as an editable install, so that the api serves the latest report of sbmlutils. The example models are part of this repository (`backend/sbml4humans/resources/`).

```bash
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

`uv sync` creates `backend/.venv` with the pinned dependencies of `uv.lock`, installs sbmlutils from the checkout and installs `sbml4humans` itself. The api answers on port 1444, e.g. <http://localhost:1444/api/examples>, the OpenAPI documentation on <http://localhost:1444/docs>. With `--reload` the server restarts on changes in `backend/`; add `--reload-dir ../../sbmlutils/src` to also restart on changes of the checkout.

**Using the latest local sbmlutils.** sbmlutils is installed editable, so a change in `../sbmlutils` (an edit, a `git pull`, a different branch) is picked up by the next request or restart, nothing needs to be reinstalled. Only the dependencies of sbmlutils are locked: after updating the checkout run `uv sync` again, it re-resolves against the `pyproject.toml` of the checkout, installs new or changed dependencies and updates `uv.lock`. Commit the changed `uv.lock` together with the change that needed it, the CI runs against the same lock.

```bash
git -C ../sbmlutils pull                   # or checkout the branch to develop against
uv sync                                    # re-lock and install its dependencies
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

Tests, linting and type checks run from the `backend` directory, the same checks run as GitHub Actions on every push:

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run ty check
```

### Frontend

The frontend builds with Vue CLI 4 and `node-sass`, which need node 14 (`frontend/.nvmrc`), e.g. with [nvm](https://github.com/nvm-sh/nvm):

```bash
cd frontend
nvm install    # reads .nvmrc, once
nvm use
npm ci
npm run serve
```

The development server runs on <http://localhost:3456> and talks to the backend api on port 1444 (`frontend/.env.development`).

## Releases

The version of sbml4humans is the version of the backend package in
`backend/sbml4humans/__init__.py`, the frontend `package.json` follows it. A
release is described in `release-notes/<version>.md`; bumping the version
commits and tags, and the tag creates the
[GitHub release](https://github.com/matthiaskoenig/sbml4humans/releases) with
these notes:

```bash
cd backend
uv run bump-my-version bump minor  # or major, patch
git push origin main --tags
```

## Funding

SBML4Humans was funded as part of [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).

## License

- Source Code: [MIT](https://opensource.org/license/MIT)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

&copy; 2021-2026 Matthias König
