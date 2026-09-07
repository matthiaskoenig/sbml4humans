# SBML4Humans

[SBML4Humans](https://sbml4humans.de) renders [SBML](https://sbml.org) models as interactive, human readable reports: a Vue frontend on top of a FastAPI backend which serves the report of [sbmlutils](https://github.com/matthiaskoenig/sbmlutils).

Until sbmlutils 0.10.0 the application lived in the sbmlutils repository. It was moved here with its history so that sbmlutils stays a library and the web application can be released independently.

## Repository layout

| path | content |
| --- | --- |
| `frontend/` | the Vue 3 application (TypeScript, Vuex, Vue Router, PrimeVue) |
| `backend/` | the FastAPI api, a thin http layer over `sbmlutils.report.sbmlinfo.SBMLDocumentInfo` |
| `nginx/` | the proxy configuration of sbml4humans.de |
| `Dockerfile`, `docker-compose-*.yml` | the containers of the backend, the frontend and the proxy |
| `deploy.md`, `deploy.sh`, `docker-purge.sh` | deployment of the server |

## Development

### Frontend and backend with docker compose

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

### Backend

```bash
uv venv --python 3.14
uv pip install -r backend/requirements.txt
uv run uvicorn --app-dir backend api:api --reload --port 1444
```

The api answers on port 1444, e.g. <http://localhost:1444/api/examples>.

### Frontend

```bash
cd frontend
npm install
npm run serve
```

The development server runs on <http://localhost:3456> and talks to the backend api.

## Funding

SBML4Humans was funded as part of [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).

## License

- Source Code: [MIT](https://opensource.org/license/MIT)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

&copy; 2021-2026 Matthias König
