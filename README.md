# SBML4Humans

[SBML4Humans](https://sbml4humans.de) renders [SBML](https://sbml.org) models as interactive, human readable reports: a Vue frontend on top of a FastAPI backend which creates the report of a model with [libsbml](https://sbml.org/software/libsbml/).

The report is self-contained: the backend reads the model with libsbml and renders the math, units and annotations itself.

## Repository layout

| path | content |
| --- | --- |
| `frontend/` | the Vue 3 application (Vite, TypeScript, Pinia, Vue Router, Tailwind CSS, Lucide icons) |
| `backend/` | the `sbml4humans` Python package: the report of a document (`sbmlinfo`, `mathml`, `units`) and the FastAPI api which serves it |
| `nginx/` | the proxy configuration of sbml4humans.de |
| `Dockerfile`, `docker-compose-*.yml` | the containers of the backend, the frontend and the proxy |
| `deploy.md`, `deploy.sh`, `docker-purge.sh` | deployment of the server |

## Development

```bash
git clone https://github.com/matthiaskoenig/sbml4humans.git
cd sbml4humans
```

### Frontend and backend with docker compose

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

The frontend answers on <http://localhost:8083>, the api on <http://localhost:1444>.

### Backend

The backend is the `sbml4humans` Python package in `backend/`, it requires Python 3.14 and [uv](https://docs.astral.sh/uv/). The report is created with libsbml, lxml (the math), pint (the units) and pymetadata (COMBINE archives and annotations); the example models are part of the package (`backend/sbml4humans/resources/`).

```bash
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

`uv sync` creates `backend/.venv` with the pinned dependencies of `uv.lock` and installs `sbml4humans` editable. The api answers on port 1444, e.g. <http://localhost:1444/api/examples>, the OpenAPI documentation on <http://localhost:1444/docs>. With `--reload` the server restarts on changes in `backend/`. A dependency change goes through `uv add`/`uv lock`, commit the updated `uv.lock` with it, the CI installs from the lock. The JSON schema of the api response is generated from the pydantic model into `frontend/src/schema/report.schema.json` with `uv run python -m sbml4humans.schema`.

Tests, linting and type checks run from the `backend` directory, the same checks run as GitHub Actions on every push:

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run ty check
```

### Frontend

The frontend needs node 24 (`frontend/.nvmrc`), e.g. with [nvm](https://github.com/nvm-sh/nvm):

```bash
cd frontend
nvm install    # reads .nvmrc, once
nvm use
npm ci
npm run dev
```

The development server runs on <http://localhost:3456> and talks to the backend api on port 1444 (`frontend/.env.development`).

Linting, type checks, unit and end to end tests run from the `frontend` directory, the same checks run as GitHub Actions on every push:

```bash
npm run lint
npm run typecheck
npm run test:unit
npm run test:e2e
```

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

- Source Code: [MIT](https://opensource.org/license/MIT), the full text is in [LICENSE](LICENSE)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

&copy; 2021-2026 Matthias König
