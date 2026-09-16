# Frontend redesign

Date: 2026-09-16. Status: approved design, sub-project 2 of 2 (follows the report data model of `2026-09-16-report-data-model-design.md`).

## Goal

Replace the Vue CLI 4 frontend, which expects the old untyped report and does not render the typed `ReportResponse`, by a new application in `frontend/` built on the typed report and the link graph. The concepts of the current report page stay (archive entries, one table per element type, search, type filter, a detail view with cross links), the user interface, the code and the toolchain are new.

## Non-goals

- No dark mode, no responsive layout of the report page (it is a desktop tool; the home and examples pages are responsive).
- No graph visualisation, no validation report, no simulation.
- No about page; the project information lives on the home page footer and in the README.
- No PWA service worker.
- No backend changes beyond what the frontend needs from the existing endpoints; if the frontend needs a backend change, it is a separate task.

## Decisions

- Rebuild in `frontend/`, the old sources are deleted in the first commit of the rebuild (the git history keeps them).
- Keep the mental model of the current report page, redesign the user interface.
- PrimeVue unstyled with the Tailwind plugin, Tailwind for everything else.
- Reports and selected elements are addressable by URL.
- Kept from the old app: the home page with upload, url and paste, the examples page, Google Analytics page views.
- Report page layout: rail on the left, tables in the middle, inspector at the bottom (layout C of the brainstorm mockups).
- Inspector: three columns, everything visible, XML behind a toggle (inspector B).
- Visual style: neutral greys and one link colour, the element type colour only as a marker (style A).

## Stack

- The current releases at the time of writing: Vite 8, Vue 3.5 with `<script setup>` and TypeScript strict, node 24 (`.nvmrc`, Dockerfiles, CI). Every dependency starts at its current release and is pinned by `package-lock.json`.
- Pinia 4 for state, Vue Router 5 for routes.
- PrimeVue 5 in unstyled mode with the `tailwindcss-primeui` plugin and Tailwind CSS 4 (`@tailwindcss/vite`), PrimeIcons. No Font Awesome.
- KaTeX renders the `latex` of every `Math` and of every units latex; the `formula` string is shown in a tooltip and is copyable.
- `json-schema-to-typescript` generates `frontend/src/types/report.ts` from `frontend/src/schema/report.schema.json` through `npm run types`. The generated file is committed; the CI regenerates it and fails on a diff, like the schema job of the backend.
- ESLint flat config with `eslint-plugin-vue` and `typescript-eslint`, Prettier, `vue-tsc --noEmit` for type checking.
- Vitest for unit tests, Playwright for end to end tests against the real backend.
- `frontend/package.json` keeps the version of the product and continues to be bumped by bump-my-version.

## Source layout

```
frontend/src/
  main.ts, App.vue, router.ts
  api/          client.ts (fetch, error contract), types.ts (re-exports of the generated types)
  stores/       report.ts, examples.ts
  report/       index.ts (ReportIndex), search.ts, columns/ (column definitions per type)
  pages/        HomePage.vue, ExamplesPage.vue, ReportPage.vue
  components/
    layout/     AppBar.vue, SplitPane.vue, LoadingState.vue, ErrorState.vue
    input/      FileUpload.vue, UrlInput.vue, PasteInput.vue
    report/     ContextBar.vue, TypeRail.vue, SearchBox.vue, ElementSection.vue, ElementTable.vue
    inspector/  InspectorPanel.vue, AttributesColumn.vue, LinksColumn.vue, AnnotationsColumn.vue, one attributes component per SBML type
    misc/       MathView.vue, UnitsView.vue, BooleanMark.vue, TypeMark.vue, ElementLink.vue, CvTermList.vue, NotesView.vue, XmlView.vue, HistoryView.vue
  data/         sbmlTypes.ts (order, labels, colours, icons and package of every element type)
  types/        report.ts (generated)
  schema/       report.schema.json (written by the backend)
```

One generic `ElementTable` driven by a column definition per type replaces the per type table components of the old app. The per type knowledge lives in `report/columns/` and in the per type attributes components of the inspector.

## Routes and URL state

| route | loads |
| --- | --- |
| `/` | home page with the upload, url and paste inputs |
| `/examples` | the examples grid from `GET /api/examples` |
| `/examples/:id` | the report of an example from `GET /api/examples/:id` |
| `/report` | with `url` in the query the report from `GET /api/url?url=`, otherwise the response of the last upload or paste held in the store |

The report page reads its view state from the query and writes every change back as a pushed route:

| query | meaning | default |
| --- | --- | --- |
| `entry` | manifest location of the SBML entry | the master entry, else the first SBML entry |
| `model` | id of the model or model definition | the main model (`kind = "model"`), else the first model |
| `pk` | pk of the selected element, opens the inspector | none, inspector closed |
| `q` | search text | empty |
| `types` | comma separated visible element types | absent, all types visible |

The browser history is the detail history: following a link pushes a route with the new `pk`, the back button returns. The old history stack is gone.

Uploads and pastes cannot be in a URL. `/report` without `url` renders the response held in the store; after a reload the store is empty and the page shows a "no report loaded" state with a link to the home page.

## State

`stores/report.ts` (Pinia):

- state: `response: ReportResponse | null`, `source: {kind: "example" | "url" | "file" | "content", id?: string, url?: string, name?: string}`, `loading: boolean`, `error: ApiError | null`, `indexes: Map<string, ReportIndex>` (per entry location, built once when the response arrives).
- actions: `loadExample(id)`, `loadUrl(url)`, `loadFile(file)`, `loadContent(text)`. Each sets `loading`, calls the api client, stores the response and builds the indexes, or stores the error. Loading the same example or url that is already loaded is a no-op, so the report page can be reloaded from the route without a second request.

`stores/examples.ts`: `examples: ExampleMetaData[]`, loaded once through `loadExamples()`.

`api/client.ts`: `getExamples()`, `getExample(id)`, `getUrl(url)`, `postFile(file)`, `postContent(text)` and `getAnnotationResource(resource)`. Every function uses `fetch`, parses the JSON and applies the error contract: a body with a non-empty `errors` array throws `ApiError{message, traceback, warnings}`; a network failure or a non-JSON body throws `ApiError` with a "backend not reachable" message. The base url comes from `import.meta.env.VITE_API_URL` (`.env.development`: `http://localhost:1444/api`, `.env.production`: `https://sbml4humans.de/api`).

`report/index.ts`: `ReportIndex` is a plain class built from a `Report`:

- `elements: Map<pk, SBase>` over every element of the report including nested ones (species references, modifier species references, kinetic laws, local parameters, event assignments, uncertainties), the document and the models.
- `byType(modelId): Map<sbmlType, SBase[]>` in list order; the document types (`SBMLDocument`, the models, external model definitions) are available separately.
- `outgoing: Map<pk, Edge[]>` and `incoming: Map<pk, Edge[]>` from `linkGraph.edges`, `nodes` from `linkGraph.nodes`.
- `modelOf(pk)`: the model id of the containing model, from the node.

Components resolve every cross reference through the index by pk, never by string building pks from ids, and every unresolved pk renders as plain text instead of a link.

`report/search.ts`: `matches(element, query)` is case insensitive over id, name, metaId, sbo, the text of the notes, the formula of every math of the element and the equation of a reaction. `q` filters the rows of every table and hides sections without a match; the rail shows `matches / total` per type while a query is active.

## Report page

**Frame.** `AppBar`: the app name linking home, the `ContextBar` and the `SearchBox`. The `ContextBar` shows the archive entry (a dropdown when the manifest has more than one SBML entry), the model (a dropdown when the document has model definitions) and the level, version and package list of the document. Below, a horizontal `SplitPane` between the rail and the content, and a vertical `SplitPane` between the tables and the inspector. The inspector is closed while no `pk` is selected; the rail width and the inspector height are stored in local storage.

**Rail** (`TypeRail`). Group "Document": the SBMLDocument, the current model and, when present, the external model definitions; clicking selects the object into the inspector. Group "Elements": every element type in specification order (function definitions, unit definitions, compartments, species, parameters, initial assignments, assignment rules, rate rules, algebraic rules, constraints, reactions, events, then the package types submodels, ports, gene products, objectives), each with its type marker, its label, a visibility checkbox and the count. Package types appear only when the document declares the package. Types with zero elements are greyed and sorted last. Clicking a label scrolls its section into view.

**Tables** (`ElementSection` with `ElementTable`). One section per visible type with elements: a header with the marker, the label and the count, and a PrimeVue DataTable with the column definition of the type, sortable columns, single row selection bound to `pk`, virtual scrolling above 200 rows. Cell rendering rules:

- ids in monospace; the id column of a row selects the row.
- references (compartment, species of a species reference, variable, symbol, units, flux bounds, model ref, port targets, associated species) are `ElementLink`s that select the target; unresolved references are plain text.
- booleans as a check mark or a dash, missing values as a dash, NaN never appears (the backend already maps it to null).
- math as `MathView` (KaTeX of the latex, tooltip with the formula), units as `UnitsView` (KaTeX of the units latex), derived units the same.
- reactions show the equation string and the kinetic law math; events show the trigger math and the number of assignments; rules show variable and math; species references are not a table, they belong to their reaction.
- notes, annotations, history and XML are inspector only.

Column sets per type are listed in `report/columns/` and follow the old tables: id, name, then the specification attributes of the type in specification order.

**Inspector** (`InspectorPanel`). Header: type marker, type label, id, name, an XML toggle and a close button; closing clears `pk`. Three columns that scroll independently:

1. `AttributesColumn`: the SBase attributes (metaId, sbo as a link to the SBO term, the comp replacement information when present) followed by the type specific attributes rendered by the per type component; nested objects (reactants, products, modifiers with stoichiometry, local parameters, event assignments, trigger, priority, delay, deletions, flux objectives, uncertainties with their uncert parameters) are small inline tables whose ids link to the nested element's own pk.
2. `LinksColumn`: "References" (outgoing edges) and "Referenced by" (incoming edges), grouped by edge kind in a fixed order, every entry an `ElementLink` pill showing the target's type marker and id. Empty groups are omitted, an element without edges shows "none".
3. `AnnotationsColumn`: the cvterms as qualifier plus resource, the resource label resolved lazily through `GET /api/annotation_resource` and cached per resource, with a link to the resource url; the notes html sanitised and rendered; the model history (creators, dates) for documents and models.

The XML toggle swaps the three columns for an `XmlView` of the element's SBML with a copy button.

## Home and examples

`HomePage`: the app name, one sentence, three inputs as tabs (upload with drag and drop and a file picker, url with a text field and the previous url remembered, paste with a text area), a link to the examples, and a footer with the project links (repository, citation, funding). Submitting shows a loading state in place; success navigates to the report route of the source (`/report?url=` for a url, `/report` for a file or paste), failure shows the api error inline with the traceback behind a toggle.

`ExamplesPage`: a text filter and a grid of cards with id, name, description and package badges, each card a router link to `/examples/:id`.

Google Analytics: page views of the routes through `vue-gtag`, with the measurement id of the old app (`G-TZ6E25RS0Q`), only in production.

## Errors and loading

Every api failure renders `ErrorState` with the message of the error contract, never a blank page. The report page while loading shows `LoadingState` with the source name. A route to an unknown example shows the api error of the example endpoint. The pk of a route that does not exist in the report closes the inspector and logs a console warning.

## Testing

- Unit (Vitest): `ReportIndex` (every element and nested element is indexed, edges are indexed both ways, unresolvable pks give no link), `search.matches`, the column definitions (every column field exists on the type), the api client (error contract, network failure), the route query round trip of the report page.
- Fixtures: `frontend/tests/fixtures/` holds recorded responses of a few examples (repressilator, a comp model, an fbc model, an omex archive) produced by `npm run fixtures` from the running backend and committed, so the unit tests run without python. The CI does not regenerate them; they are refreshed by hand when the model changes.
- End to end (Playwright, against the running backend): every example loads through the examples page and renders its sections; on the repressilator select a species, follow a "referenced by" link, use the back button; search filters the tables; toggle a type off; upload a file; paste content; load a url; the error path of an invalid url shows the message; the archive dropdown of an omex example switches the entry.

## CI and deployment

- `.github/workflows/ci.yml` gets a `frontend` job on node 24: `npm ci`, `npm run types` plus `git diff --exit-code`, `npm run lint`, `npm run typecheck`, `npm run test:unit`, `npm run build`; and an `e2e` job that installs the backend with uv, starts uvicorn, and runs `npm run test:e2e`. The release job needs both.
- `frontend/Dockerfile-develop` and `Dockerfile-production` build on `node:24`; production copies `dist/` into the nginx volume as today. `docker-compose-develop.yml` serves the Vite dev server on the same port (3456, `--host`). The nginx configuration is unchanged.
- `frontend/README.md`, the root `README.md` and `CLAUDE.md` describe the new stack, commands and layout; the note that the frontend does not render reports is removed.

## Files

- deleted: everything under `frontend/` except `src/schema/report.schema.json`, `.env.development`, `.env.production`, `public/` assets that are still used (favicon, logos) and the README, which is rewritten.
- new: the layout above, `frontend/vite.config.ts`, `frontend/src/assets/main.css` (the Tailwind 4 import and the design tokens: colours, the type colours, spacing, fonts), `frontend/eslint.config.js`, `frontend/playwright.config.ts`, `frontend/vitest.config.ts`, `frontend/tests/`.
- adapted: `.github/workflows/ci.yml`, `frontend/Dockerfile-develop`, `frontend/Dockerfile-production`, `docker-compose-develop.yml`, `docker-compose-production.yml`, `frontend/README.md`, `README.md`, `CLAUDE.md`, `.gitignore` (`.superpowers/`).
