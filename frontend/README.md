# SBML4Humans frontend

The Vue 3 application of [SBML4Humans](https://sbml4humans.de), the interactive report of SBML models. It renders the typed report the backend api in `../backend` serves. The documentation of the application is at [matthiaskoenig.github.io/sbml4humans](https://matthiaskoenig.github.io/sbml4humans/), the repository layout, the docker compose setup, the checks, the branches and the releases are in [`docs/development.md`](../docs/development.md).

## Development

The frontend talks to the backend api on port 1444, so start the backend first:

```bash
cd backend
uv sync
uv run uvicorn sbml4humans.api:api --reload --port 1444
```

The frontend needs node 24 (`.nvmrc`), e.g. with [nvm](https://github.com/nvm-sh/nvm):

```bash
cd frontend
nvm install    # reads .nvmrc, once
nvm use
npm ci
npm run dev
```

The development server runs on <http://localhost:3456> and hot reloads on changes; the api url is `VITE_API_URL` in `.env.development`, the production url in `.env.production`. Further scripts:

```bash
npm run build        # type check and production build into dist/
npm run typecheck    # vue-tsc
npm run lint         # eslint and prettier --check
npm run format       # prettier --write
npm run test:unit    # vitest
npm run test:e2e     # playwright against the running backend (npx playwright install chromium once)
npm run types        # regenerate src/types/report.ts from src/schema/report.schema.json
npm run fixtures     # record tests/fixtures/*.json from the running backend
npm run screenshots  # retake docs/images/*.png against the running backend and the dev server
```

`package-lock.json` is committed and the containers install with `npm ci`, so every build gets the same versions. Commit the changed lock with the change that needed it.

## Layout

- `src/api/`: the fetch client with the error contract and the report types (generated, `npm run types`).
- `src/stores/`: the Pinia stores of the report and the examples.
- `src/report/`: `ReportIndex` (every element by pk, the edges of the link graph), the search, the view state of the report page (route query) and the table columns per element type.
- `src/pages/`: home (upload, url, paste), examples, report.
- `src/components/`: `layout/` (app bar, split panes, states), `input/`, `report/` (context bar, type rail, search, element tables), `inspector/` (attributes per type, links, annotations), `misc/` (math, units, links, notes, xml).
- `src/data/`: order, labels, colours and icons of the SBML types and the edge kinds.
- `tests/unit/` (vitest with the recorded fixtures), `tests/e2e/` (playwright).

## Technology

- [Vite](https://vite.dev/) 8, [Vue 3](https://vuejs.org/) with `<script setup>` and TypeScript, [Pinia](https://pinia.vuejs.org/), [Vue Router](https://router.vuejs.org/).
- [Tailwind CSS](https://tailwindcss.com/) 4 for the styling with [Lucide](https://lucide.dev/) icons and [Floating UI](https://floating-ui.com/) for the tooltips; the tables, the dropdowns and the tooltip directive are components of the application. [KaTeX](https://katex.org/) renders the math and units, DOMPurify sanitises the notes.
- ESLint, Prettier, `vue-tsc`, Vitest, Playwright.
