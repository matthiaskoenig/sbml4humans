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

### Frontend and backend with docker compose

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

The backend container installs sbmlutils from its latest `develop` branch.

### Backend

The backend is the Python package in `backend/`, it requires Python 3.14. For
development it runs against the [sbmlutils](https://github.com/matthiaskoenig/sbmlutils)
checkout next to this repository (see `[tool.uv.sources]` in
`backend/pyproject.toml`): the checkout provides the curated BioModels served as
examples, which are not part of the sbmlutils distribution on PyPI.

```bash
git clone https://github.com/matthiaskoenig/sbmlutils.git ../sbmlutils
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

The api answers on port 1444, e.g. <http://localhost:1444/api/examples>, the
OpenAPI documentation on <http://localhost:1444/docs>.

Tests, linting and type checks run from the `backend` directory, the same checks
run as GitHub Actions on every push:

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run ty check
```

### Frontend

```bash
cd frontend
npm install
npm run serve
```

The development server runs on <http://localhost:3456> and talks to the backend api.

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
