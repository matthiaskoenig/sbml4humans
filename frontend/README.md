# SBML4Humans
This document describes the technology and how to setup the development 
environment for the SBML4Humans report.

## Project setup for development

### Start backend API and frontend (docker compose)
The simplest setup is to start the frontend and backend via the docker-compose scripts.

```bash
sudo docker compose -f docker-compose-develop.yml build --no-cache
sudo docker compose -f docker-compose-develop.yml up
```

Alternatively the backend and frontend can be run directly on the machine. This most likely requires updates of the local `node` and `npm` packages.


### Start backend API (local)
The backend is the `sbml4humans` Python package in `backend/`, it requires
Python 3.14 and [uv](https://docs.astral.sh/uv/). For development it runs
against the [sbmlutils](https://github.com/matthiaskoenig/sbmlutils) checkout
next to this repository, which provides the curated BioModels served as examples
(see the [main README](../README.md) for details).

```bash
git clone https://github.com/matthiaskoenig/sbmlutils.git ../sbmlutils
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

This will run the API on port 1444. Check that the API is running using a browser
http://localhost:1444/api/examples


### Start frontend (local)
**Install all dependencies**  
```
cd frontend
npm install
```

**Compiles and hot-reloads for development**
```
npm run serve
```
This starts the frontend server on http://localhost:3456/ which communicates with 
the running backend API.


## Technology
1. Backend API: ```sbmlutils``` Python package served using FastAPI service [https://fastapi.tiangolo.com/]
2. Frontend User Interface: Build using Vue.js 3 [https://vuejs.org/]
    - TypeScript + SCSS
    - Vuex
    - Vue Router
3. Frontend UI/UX Package: Ant Design Vue [https://www.antdv.com/docs/vue/introduce/]

## Vue.js devtools
Vue 3 is only working with the beta version of the devtools available from
https://github.com/vuejs/vue-devtools/releases
To install the devtools use the `xpi` file from the download and install in Firefox.
