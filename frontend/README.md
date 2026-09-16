# SBML4Humans frontend

The Vue 3 application of [SBML4Humans](https://sbml4humans.de), the interactive report of SBML models. It renders the report the backend api in `../backend` serves, see the [main README](../README.md) for the repository layout, the docker compose setup and the releases.

## Development

The frontend talks to the backend api on port 1444, so start the backend first. Both repositories must be checked out next to each other (`sbml4humans` and `sbmlutils`), the backend develops against the sbmlutils checkout:

```bash
git clone https://github.com/matthiaskoenig/sbml4humans.git
git clone https://github.com/matthiaskoenig/sbmlutils.git
```

### Backend api

The backend is the `sbml4humans` Python package in `../backend`, it requires Python 3.14 and [uv](https://docs.astral.sh/uv/). `uv sync` installs the pinned dependencies and the `../../sbmlutils` checkout as an editable package, so that the api serves the latest report of sbmlutils:

```bash
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

Check that the api is running on <http://localhost:1444/api/examples>. To develop against the latest local sbmlutils update the checkout and sync again, code changes of the checkout are live without a reinstall, `uv sync` only picks up changed dependencies of sbmlutils and updates `uv.lock`:

```bash
git -C ../sbmlutils pull
uv sync
```

### Frontend

The frontend builds with Vue CLI 4 (webpack 4) and `node-sass`, which require node 14, the version of `.nvmrc` and of the docker containers. With [nvm](https://github.com/nvm-sh/nvm):

```bash
cd frontend
nvm install    # reads .nvmrc, once
nvm use
npm ci
npm run serve
```

The development server runs on <http://localhost:3456> and hot reloads on changes; the api url is configured in `.env.development`, the production url in `.env.production`. Further scripts:

```bash
npm run build      # production build into dist/
npm run lint       # eslint with prettier
npm run test:unit  # jest
npm run test:e2e   # cypress
```

`package-lock.json` is committed and the containers install with `npm ci`, so every build gets the same versions. `npm install` updates the lock within the ranges of `package.json`, commit the changed lock with the change that needed it. A dependency whose new release breaks the webpack 4 build is capped in `package.json`, e.g. `vue-router` below 4.6.4, which ships optional chaining that webpack 4 cannot parse.

### Docker compose

Both services can also run in containers from the repository root, the backend then installs sbmlutils from its `develop` branch on GitHub:

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

The frontend answers on <http://localhost:8083>, the api on <http://localhost:1444>.

## Technology

- Backend api: [FastAPI](https://fastapi.tiangolo.com/), a thin http layer over the report of the [sbmlutils](https://github.com/matthiaskoenig/sbmlutils) Python package.
- Frontend: [Vue.js 3](https://vuejs.org/) with TypeScript and SCSS, [Vuex](https://vuex.vuejs.org/) for the state, [Vue Router](https://router.vuejs.org/) for the routes.
- UI components: [PrimeVue](https://primevue.org/) with PrimeFlex and PrimeIcons, Font Awesome icons, KaTeX for the math.
- Vue devtools: the [Vue.js devtools](https://devtools.vuejs.org/) browser extension works with the development server.
