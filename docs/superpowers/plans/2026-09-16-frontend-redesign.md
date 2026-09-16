# Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Vue CLI 4 frontend by a Vite 8 / Vue 3.5 application that renders the typed `ReportResponse` of the backend: home page with upload, url and paste, examples page, and a report page with a type rail, one table per element type, search, and an inspector with cross links driven by the link graph.

**Architecture:** The api client fetches the typed report and applies the error contract; `ReportIndex` indexes every element by pk and every edge in both directions; components resolve cross references only through the index. The report page keeps its view state (entry, model, selected pk, search, visible types) in the route query. One generic `ElementTable` driven by a column definition per type renders the tables, one small attributes component per SBML type renders the inspector.

**Tech Stack:** node 24, Vite 8, Vue 3.5 (`<script setup>`, TypeScript 5.9 strict), Pinia 4, Vue Router 5, PrimeVue 4.5.5 unstyled (DataTable, Select, Tooltip only) with `tailwindcss-primeui`, Tailwind CSS 4, PrimeIcons, KaTeX, DOMPurify, `json-schema-to-typescript`, ESLint 10 flat config with `eslint-plugin-vue` and `typescript-eslint`, Prettier, `vue-tsc`, Vitest 5, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-16-frontend-redesign-design.md`

## Global Constraints

- Everything frontend runs from `frontend/` on node 24 (`source ~/.nvm/nvm.sh && nvm use` reads `.nvmrc`). Never run the old node 14.
- `npm run lint`, `npm run typecheck`, `npm run test:unit` and `npm run build` must pass after every task. Zero ESLint warnings, zero type errors.
- Every dependency is added at its current release with `npm install <pkg>@<version>` and pinned by the committed `package-lock.json`. TypeScript stays at `~5.9.3` (`typescript-eslint` supports TypeScript below 6.1 only). PrimeVue stays at `^4.5.5` (MIT; PrimeVue 5 is commercial).
- The backend is not changed. The frontend consumes the endpoints of `backend/sbml4humans/api.py` as they are: `GET /api/examples` -> `{examples: ExampleMetaData[]}`, `GET /api/examples/{id}`, `POST /api/file` (multipart field `source`), `GET /api/url?url=`, `POST /api/content` (raw body), `GET /api/annotation_resource?resource=`.
- Error contract: every failure is a status 200 body `{"errors": [message, traceback], "warnings": [], "info": {...}}`. The client throws `ApiError` for it; the pages render `ErrorState`, never a blank page.
- Components never build a pk from an id. A cross reference is resolved through `ReportIndex.resolve(sourcePk, edgeKind, id)` or through the edges; an unresolved reference renders as plain text.
- Generated files: `src/types/report.ts` (`npm run types`, committed, the CI diffs it), `tests/fixtures/*.json` (`npm run fixtures`, committed, refreshed by hand).
- Vue components use `<script setup lang="ts">` and `defineProps` with type literals. Files are formatted by Prettier (`npm run format`).
- Text and comments: no em dash, plain dash only. Markdown without hard line wraps.
- Commit messages: imperative, capitalised, one line, no prefix, no co-author lines (like `Add the design of the frontend redesign`). Commit after every task, only files of the task. Never edit `release-notes/`, never bump the version by hand.
- Test ids: every element an end to end test needs carries a `data-testid` (listed in the tasks), so tests never depend on classes.

---

## File structure

```
frontend/
  .nvmrc (24), .env.development, .env.production, .gitignore, .prettierrc.json, .prettierignore
  package.json, package-lock.json, index.html
  vite.config.ts, vitest.config.ts, playwright.config.ts, eslint.config.js
  tsconfig.json, tsconfig.app.json, tsconfig.node.json
  Dockerfile-develop, Dockerfile-production, README.md, privacy_notice.md
  public/            favicon.ico, favicon-16x16.png, favicon-32x32.png, apple-touch-icon.png, android-chrome-*.png, site.webmanifest, robots.txt
  scripts/fixtures.mjs
  src/
    main.ts, App.vue, router.ts, env.d.ts
    assets/main.css, assets/primevue.ts
    api/client.ts, api/types.ts, api/annotations.ts
    stores/report.ts, stores/examples.ts
    report/index.ts, report/search.ts, report/query.ts, report/view.ts, report/context.ts, report/columns/index.ts, report/columns/<type>.ts
    pages/HomePage.vue, pages/ExamplesPage.vue, pages/ReportPage.vue
    components/layout/AppBar.vue, SplitPane.vue, LoadingState.vue, ErrorState.vue
    components/input/FileUpload.vue, UrlInput.vue, PasteInput.vue
    components/report/ContextBar.vue, TypeRail.vue, SearchBox.vue, ElementSection.vue, ElementTable.vue, ElementCell.vue
    components/inspector/InspectorPanel.vue, AttributesColumn.vue, LinksColumn.vue, AnnotationsColumn.vue, AttributeRow.vue, NestedTable.vue, attributes/<Type>Attributes.vue, attributes/index.ts
    components/misc/MathView.vue, UnitsView.vue, BooleanMark.vue, TypeMark.vue, ElementLink.vue, CvTermList.vue, NotesView.vue, XmlView.vue, HistoryView.vue, ValueText.vue
    data/sbmlTypes.ts, data/edgeKinds.ts
    types/report.ts (generated)
    schema/report.schema.json (written by the backend, untouched)
  tests/
    fixtures/*.json, unit/fixtures.ts, unit/*.test.ts, e2e/*.spec.ts
```

Responsibilities:

- `api/client.ts`: the only module that calls `fetch`; `ApiError` and the error contract.
- `api/types.ts`: re-exports of the generated types plus the hand written unions (`SBase`, `SbmlType`, `ElementType`, `ModelListKey`) and the shapes of the non-report endpoints (`ExampleMetaData`, `AnnotationInfo`).
- `report/index.ts`: `ReportIndex`, pure data, no Vue.
- `report/search.ts`: `matches(element, query)`, pure.
- `report/query.ts`: `ViewState` <-> route query, pure.
- `report/view.ts`: `useReportView()`, the router side of the view state.
- `report/context.ts`: provide/inject of the current `ReportIndex`.
- `report/columns/`: `ColumnDef` and the columns of every element type.
- `data/sbmlTypes.ts`: order, labels, colours, icons, package and model list key of every SBML type.
- `data/edgeKinds.ts`: order and labels of the edge kinds.
- `stores/`: Pinia stores, the report store owns the response and the indexes.
- `components/`: presentation only; every lookup goes through the injected index.

---

### Task 1: Vite scaffold replacing the Vue CLI frontend

**Files:**
- Delete: everything under `frontend/` except `src/schema/report.schema.json`, `.env.development`, `.env.production`, `privacy_notice.md`, `public/` (minus `public/index.html` and `public/about.txt`), `README.md` (rewritten in Task 13), `Dockerfile-develop`, `Dockerfile-production` (rewritten in Task 13)
- Create: `frontend/.nvmrc`, `frontend/package.json`, `frontend/index.html`, `frontend/vite.config.ts`, `frontend/vitest.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`, `frontend/eslint.config.js`, `frontend/.prettierrc.json`, `frontend/.prettierignore`, `frontend/.gitignore`, `frontend/src/main.ts`, `frontend/src/App.vue`, `frontend/src/env.d.ts`, `frontend/src/assets/main.css`, `frontend/src/assets/primevue.ts`
- Test: `frontend/tests/unit/smoke.test.ts`

**Interfaces:**
- Produces: the `npm run` scripts `dev`, `build`, `preview`, `typecheck`, `lint`, `format`, `types`, `fixtures`, `test:unit`, `test:e2e`; the `@/` alias to `src/`; `import.meta.env.VITE_API_URL`; the PrimeVue options `primevueOptions` (unstyled, global pass through for `datatable`, `column`, `select`, `tooltip`).

- [ ] **Step 1: Switch to node 24 and delete the old frontend**

```bash
cd frontend
source ~/.nvm/nvm.sh && nvm use 24 && node --version   # v24.x
git rm -r -q babel.config.js cypress.json package.json package-lock.json tsconfig.json vue.config.js src tests public/index.html public/about.txt
git checkout HEAD -- src/schema/report.schema.json   # keep the schema
rm -rf node_modules
echo 24 > .nvmrc
git status --short | head
```

Expected: `src/` contains only `schema/report.schema.json`; `.env.*`, `privacy_notice.md`, `README.md`, `Dockerfile-*` and the `public/` icons remain.

- [ ] **Step 2: Rewrite the env files**

`frontend/.env.development`:
```
VITE_API_URL=http://localhost:1444/api
```

`frontend/.env.production`:
```
VITE_API_URL=https://sbml4humans.de/api
```

- [ ] **Step 3: Write package.json and install**

`frontend/package.json` (the version stays `0.2.0`, bump-my-version rewrites it):
```json
{
  "name": "sbml4humans",
  "version": "0.2.0",
  "private": true,
  "type": "module",
  "author": "Matthias König <konigmatt@googlemail.com> (https://livermetabolism.com)",
  "engines": {
    "node": ">=24"
  },
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit -p tsconfig.app.json && vite build",
    "preview": "vite preview",
    "typecheck": "vue-tsc --noEmit -p tsconfig.app.json && tsc --noEmit -p tsconfig.node.json",
    "lint": "eslint . && prettier --check .",
    "format": "prettier --write .",
    "types": "json2ts --input src/schema/report.schema.json --output src/types/report.ts --additionalProperties false --bannerComment \"/* eslint-disable */\\n// Generated by 'npm run types' from src/schema/report.schema.json, do not edit.\" && prettier --write src/types/report.ts",
    "fixtures": "node scripts/fixtures.mjs",
    "test:unit": "vitest run",
    "test:e2e": "playwright test"
  }
}
```

Install the dependencies at their current releases (the versions checked on 2026-09-16, npm writes the caret ranges and the lock):
```bash
npm install vue@3.5.42 vue-router@5.3.1 pinia@4.0.3 primevue@4.5.5 primeicons@8.0.1 tailwindcss@4.3.3 tailwindcss-primeui@0.6.1 katex@0.18.7 dompurify@3.4.15 vue-gtag@3.7.1
npm install --save-dev vite@8.3.0 @vitejs/plugin-vue@6.0.9 @tailwindcss/vite@4.3.3 typescript@5.9.3 vue-tsc@3.3.11 @vue/tsconfig@0.9.1 @tsconfig/node24@24.0.5 @types/node@24 @types/katex@0.16.8 eslint@10.10.0 @eslint/js@10.0.1 globals@17.12.0 eslint-plugin-vue@10.11.0 vue-eslint-parser@10 typescript-eslint@8.70.0 eslint-config-prettier@10.1.8 prettier@3.9.7 vitest@5.0.1 @vue/test-utils@2.5.1 jsdom@30.0.1 @playwright/test@1.63.0 json-schema-to-typescript@16.0.0
sed -i 's/"typescript": "^5.9.3"/"typescript": "~5.9.3"/' package.json
npx playwright install chromium
```

Expected: `package-lock.json` with `lockfileVersion: 3`, no peer dependency errors. If npm reports an `ERESOLVE` conflict, read the message, it names the two packages; pick the newest version of the demanding package that satisfies the other, never `--force`.

- [ ] **Step 4: Write the TypeScript and Vite configuration**

`frontend/tsconfig.json`:
```json
{
  "files": [],
  "references": [{ "path": "./tsconfig.app.json" }, { "path": "./tsconfig.node.json" }]
}
```

`frontend/tsconfig.app.json`:
```json
{
  "extends": "@vue/tsconfig/tsconfig.dom.json",
  "include": ["src/**/*", "src/**/*.vue", "tests/unit/**/*"],
  "exclude": ["src/**/__tests__/*"],
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] },
    "types": ["vite/client"],
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  }
}
```

`frontend/tsconfig.node.json`:
```json
{
  "extends": "@tsconfig/node24/tsconfig.json",
  "include": ["vite.config.ts", "vitest.config.ts", "playwright.config.ts", "tests/e2e/**/*"],
  "compilerOptions": {
    "composite": true,
    "noEmit": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "types": ["node"]
  }
}
```

`frontend/vite.config.ts`:
```ts
import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: { port: 3456, host: true, strictPort: true },
  preview: { port: 3456, host: true, strictPort: true },
});
```

`frontend/vitest.config.ts`:
```ts
import { fileURLToPath, URL } from "node:url";

import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      include: ["tests/unit/**/*.test.ts"],
      root: fileURLToPath(new URL("./", import.meta.url)),
    },
  }),
);
```

`frontend/src/env.d.ts`:
```ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}
```

- [ ] **Step 5: Write the lint and format configuration**

`frontend/eslint.config.js`:
```js
import js from "@eslint/js";
import prettier from "eslint-config-prettier/flat";
import { defineConfig } from "eslint/config";
import pluginVue from "eslint-plugin-vue";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
  {
    ignores: ["dist/", "node_modules/", "src/types/report.ts", "playwright-report/", "test-results/"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  {
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: { parser: tseslint.parser, extraFileExtensions: [".vue"], sourceType: "module" },
    },
  },
  {
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    rules: {
      "vue/multi-word-component-names": "off",
      "@typescript-eslint/consistent-type-imports": "error",
    },
  },
  prettier,
]);
```

`frontend/.prettierrc.json`:
```json
{
  "printWidth": 100,
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all"
}
```

`frontend/.prettierignore`:
```
dist/
node_modules/
package-lock.json
playwright-report/
test-results/
src/schema/report.schema.json
```

`frontend/.gitignore`:
```
node_modules/
dist/
playwright-report/
test-results/
.env.local
.env.*.local
npm-debug.log*
```

- [ ] **Step 6: Write the entry point, the stylesheet and the PrimeVue options**

`frontend/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SBML4Humans</title>
    <meta name="description" content="Interactive, human readable reports of SBML models." />
    <link rel="icon" href="/favicon.ico" />
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
    <link rel="manifest" href="/site.webmanifest" />
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

`frontend/src/assets/main.css` (the design tokens: neutral greys, one link colour, the type colours only as markers):
```css
@import "tailwindcss";
@import "tailwindcss-primeui";
@import "primeicons/primeicons.css";
@import "katex/dist/katex.min.css";

@theme {
  --font-sans: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  --color-link: #1d4ed8;
  --color-link-hover: #1e40af;
  --color-selected: #dbeafe;
}

html,
body,
#app {
  height: 100%;
}

body {
  @apply bg-white text-gray-900 antialiased;
}

.katex {
  font-size: 1em;
}
```

`frontend/src/assets/primevue.ts` (the pass through of the three PrimeVue components in use; every other control is a native element):
```ts
import type { PrimeVueConfiguration } from "primevue/config";

/** Global pass through classes of the PrimeVue components in unstyled mode. */
export const primevueOptions: PrimeVueConfiguration = {
  unstyled: true,
  ptOptions: { mergeSections: true, mergeProps: true },
  pt: {
    datatable: {
      root: "text-sm",
      tableContainer: "overflow-auto",
      table: "w-full border-collapse",
      thead: "sticky top-0 z-10 bg-gray-50",
      headerRow: "border-b border-gray-200",
      bodyRow: ({ context }: { context: { selected: boolean } }) => ({
        class: [
          "cursor-pointer border-b border-gray-100",
          context.selected ? "bg-selected" : "hover:bg-gray-50",
        ],
      }),
      emptyMessage: "text-gray-500",
    },
    column: {
      headerCell: "px-3 py-2 text-left font-medium text-gray-600 whitespace-nowrap select-none",
      columnHeaderContent: "flex items-center gap-1",
      columnTitle: "",
      sort: "text-gray-400",
      sortIcon: "size-3",
      bodyCell: "px-3 py-1.5 align-top whitespace-nowrap",
    },
    select: {
      root: "inline-flex items-center gap-2 rounded border border-gray-300 bg-white px-2 py-1 text-sm hover:border-gray-400 cursor-pointer",
      label: "truncate max-w-64",
      dropdown: "flex items-center text-gray-500",
      dropdownIcon: "size-3",
      overlay: "mt-1 rounded border border-gray-200 bg-white shadow-lg text-sm",
      listContainer: "max-h-80 overflow-auto",
      list: "py-1",
      option: ({ context }: { context: { selected: boolean; focused: boolean } }) => ({
        class: [
          "px-3 py-1.5 cursor-pointer whitespace-nowrap",
          context.selected ? "bg-selected" : context.focused ? "bg-gray-100" : "hover:bg-gray-50",
        ],
      }),
      optionLabel: "",
      emptyMessage: "px-3 py-1.5 text-gray-500",
    },
    tooltip: {
      root: "absolute z-50 max-w-md",
      text: "rounded bg-gray-900 px-2 py-1 font-mono text-xs text-white shadow",
      arrow: "hidden",
    },
  },
};
```

The section names are those of the Pass Through tables of the PrimeVue 4 documentation (`https://v4.primevue.org/datatable/#pt`, `/select/#pt`, `/tooltip/#pt`). If the browser shows an unstyled section after Task 9, look the name up there and add it here.

`frontend/src/main.ts` (router and stores arrive in Task 5, gtag in Task 6):
```ts
import { createApp } from "vue";
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";

import App from "@/App.vue";
import { primevueOptions } from "@/assets/primevue";
import "@/assets/main.css";

const app = createApp(App);
app.use(PrimeVue, primevueOptions);
app.directive("tooltip", Tooltip);
app.mount("#app");
```

`frontend/src/App.vue`:
```vue
<script setup lang="ts"></script>

<template>
  <div class="flex h-full flex-col">
    <main class="flex min-h-0 flex-1 flex-col">
      <h1 class="p-4 text-xl font-semibold">SBML4Humans</h1>
    </main>
  </div>
</template>
```

- [ ] **Step 7: Write the smoke test**

`frontend/tests/unit/smoke.test.ts`:
```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "@/App.vue";

describe("App", () => {
  it("renders the app name", () => {
    const wrapper = mount(App);
    expect(wrapper.text()).toContain("SBML4Humans");
  });
});
```

- [ ] **Step 8: Run every script**

```bash
npm run format
npm run lint
npm run typecheck
npm run test:unit
npm run build
```

Expected: all four pass, `dist/index.html` exists. Then `npm run dev` and open `http://localhost:3456`: the heading is rendered with the system font, no console error. Stop the dev server.

- [ ] **Step 9: Commit**

```bash
cd /home/mkoenig/git/sbml4humans
git add -A frontend
git commit -m "Replace the Vue CLI frontend by a Vite scaffold"
```

---

### Task 2: Generated report types and the SBML type data

**Files:**
- Create: `frontend/src/types/report.ts` (generated), `frontend/src/api/types.ts`, `frontend/src/data/sbmlTypes.ts`, `frontend/src/data/edgeKinds.ts`
- Test: `frontend/tests/unit/sbmlTypes.test.ts`

**Interfaces:**
- Consumes: `npm run types` of Task 1, `src/schema/report.schema.json`.
- Produces: every interface of the schema (`ReportResponse`, `Report`, `Model`, `Species`, ..., `Edge`, `EdgeKind`, `Node`, `Math`) from `@/api/types`; the unions `SBase`, `SbmlType`, `ElementType`, `DocumentElement`, `NestedElement`, `Rule`, `ModelListKey`; `ExampleMetaData`, `AnnotationInfo`; `ELEMENT_TYPES`, `DOCUMENT_TYPES`, `NESTED_TYPES`, `SBML_TYPES`, `typeInfo(type)`, `isElementType(type)` from `@/data/sbmlTypes`; `EDGE_KINDS`, `edgeKindLabel(kind)` from `@/data/edgeKinds`.

- [ ] **Step 1: Generate the types**

```bash
cd frontend && npm run types && head -30 src/types/report.ts && grep -c "^export " src/types/report.ts
```

Expected: the banner comment, then `export interface ReportResponse { uid: string; manifest: Manifest; reports: { [k: string]: ReportEntry } }` and one interface per `$defs` entry (about 55 exports). `sbmlType` of the SBML objects is a literal, e.g. `sbmlType?: "Species"`, and `EdgeKind` a union of string literals. Fields with a default are optional in the generated type; the backend always sends every field, components read them with `?? null`.

- [ ] **Step 2: Write the failing test of the type data**

`frontend/tests/unit/sbmlTypes.test.ts`:
```ts
import { describe, expect, it } from "vitest";

import { EDGE_KINDS, edgeKindLabel } from "@/data/edgeKinds";
import {
  DOCUMENT_TYPES,
  ELEMENT_TYPES,
  NESTED_TYPES,
  SBML_TYPES,
  isElementType,
  typeInfo,
} from "@/data/sbmlTypes";

describe("sbml types", () => {
  it("lists the element types in specification order", () => {
    expect(ELEMENT_TYPES.map((t) => t.type)).toEqual([
      "FunctionDefinition",
      "UnitDefinition",
      "Compartment",
      "Species",
      "Parameter",
      "InitialAssignment",
      "AssignmentRule",
      "RateRule",
      "AlgebraicRule",
      "Constraint",
      "Reaction",
      "Event",
      "Submodel",
      "Port",
      "GeneProduct",
      "Objective",
    ]);
  });

  it("knows every type once", () => {
    const all = [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES];
    expect(new Set(all.map((t) => t.type)).size).toBe(all.length);
    expect(Object.keys(SBML_TYPES)).toHaveLength(all.length);
    for (const info of all) {
      expect(typeInfo(info.type)).toBe(info);
      expect(info.color).toMatch(/^#[0-9a-f]{6}$/);
      expect(info.icon).toMatch(/^pi-/);
    }
  });

  it("marks the package of the comp and fbc types", () => {
    expect(typeInfo("Submodel").pkg).toBe("comp");
    expect(typeInfo("Port").pkg).toBe("comp");
    expect(typeInfo("GeneProduct").pkg).toBe("fbc");
    expect(typeInfo("Objective").pkg).toBe("fbc");
    expect(typeInfo("Species").pkg).toBe("core");
  });

  it("maps every element type to its model list", () => {
    for (const info of ELEMENT_TYPES) {
      expect(info.listKey).toMatch(/^listOf/);
    }
    expect(typeInfo("RateRule").listKey).toBe("listOfRules");
    expect(isElementType("Species")).toBe(true);
    expect(isElementType("SBMLDocument")).toBe(false);
  });

  it("orders and labels the edge kinds", () => {
    expect(EDGE_KINDS[0]).toBe("compartment");
    expect(EDGE_KINDS).toHaveLength(17);
    expect(edgeKindLabel("fluxBound")).toBe("flux bound");
    expect(edgeKindLabel("replacedBy")).toBe("replaced by");
  });
});
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `npx vitest run tests/unit/sbmlTypes.test.ts`
Expected: FAIL, cannot resolve `@/data/sbmlTypes`.

- [ ] **Step 4: Write api/types.ts**

`frontend/src/api/types.ts`:
```ts
/** The report types generated from the JSON schema plus the unions the components work with. */
import type {
  AlgebraicRule,
  AssignmentRule,
  Compartment,
  Constraint,
  Event,
  EventAssignment,
  ExternalModelDefinition,
  FunctionDefinition,
  GeneProduct,
  InitialAssignment,
  KineticLaw,
  LocalParameter,
  Model,
  ModifierSpeciesReference,
  Objective,
  Parameter,
  Port,
  RateRule,
  Reaction,
  SBMLDocument,
  Species,
  SpeciesReference,
  Submodel,
  Uncertainty,
  UnitDefinition,
} from "@/types/report";

export type * from "@/types/report";

/** The objects of the document group of the rail. */
export type DocumentElement = SBMLDocument | Model | ExternalModelDefinition;

/** The objects with a table of their own. */
export type SbmlElement =
  | FunctionDefinition
  | UnitDefinition
  | Compartment
  | Species
  | Parameter
  | InitialAssignment
  | AssignmentRule
  | RateRule
  | AlgebraicRule
  | Constraint
  | Reaction
  | Event
  | Submodel
  | Port
  | GeneProduct
  | Objective;

/** The objects nested in another object, reachable through the inspector only. */
export type NestedElement =
  | SpeciesReference
  | ModifierSpeciesReference
  | KineticLaw
  | LocalParameter
  | EventAssignment
  | Uncertainty;

export type SBase = DocumentElement | SbmlElement | NestedElement;
export type Rule = AssignmentRule | RateRule | AlgebraicRule;

export type SbmlType = NonNullable<SBase["sbmlType"]>;
export type ElementType = NonNullable<SbmlElement["sbmlType"]>;
export type DocumentElementType = NonNullable<DocumentElement["sbmlType"]>;
export type NestedElementType = NonNullable<NestedElement["sbmlType"]>;

/** The keys of the SBML lists of a model. */
export type ModelListKey = {
  [K in keyof Model]-?: K extends `listOf${string}` ? K : never;
}[keyof Model];

/** `GET /api/examples` entry. */
export interface ExampleMetaData {
  id: string;
  name: string | null;
  description: string | null;
  packages: string[];
}

/** `GET /api/annotation_resource` body (snake_case, as pymetadata returns it). */
export interface AnnotationInfo {
  resource: string;
  resource_normalized: string | null;
  collection: string | null;
  term: string | null;
  label: string | null;
  description: string | null;
  url: string | null;
  synonyms: string[];
  xrefs: string[];
  errors: string[];
  warnings: string[];
}
```

- [ ] **Step 5: Write the type data**

`frontend/src/data/sbmlTypes.ts` (colours of the old app, PrimeIcons instead of Font Awesome):
```ts
import type {
  DocumentElementType,
  ElementType,
  ModelListKey,
  NestedElementType,
  SbmlType,
} from "@/api/types";

export type SbmlPackage = "core" | "comp" | "fbc" | "distrib";

export interface SbmlTypeInfo<T extends SbmlType = SbmlType> {
  type: T;
  /** Singular label. */
  label: string;
  /** Plural label, the section header. */
  plural: string;
  /** Marker colour. */
  color: string;
  /** PrimeIcons class without the `pi` prefix. */
  icon: string;
  pkg: SbmlPackage;
}

export interface ElementTypeInfo extends SbmlTypeInfo<ElementType> {
  /** The list of the model holding the elements. */
  listKey: ModelListKey;
}

export const DOCUMENT_TYPES: readonly SbmlTypeInfo<DocumentElementType>[] = [
  { type: "SBMLDocument", label: "Document", plural: "Documents", color: "#fcd090", icon: "pi-file", pkg: "core" },
  { type: "Model", label: "Model", plural: "Models", color: "#66c2a5", icon: "pi-sitemap", pkg: "core" },
  { type: "ExternalModelDefinition", label: "External model definition", plural: "External model definitions", color: "#66c2a5", icon: "pi-external-link", pkg: "comp" },
];

export const ELEMENT_TYPES: readonly ElementTypeInfo[] = [
  { type: "FunctionDefinition", label: "Function definition", plural: "Function definitions", color: "#e6f598", icon: "pi-code", pkg: "core", listKey: "listOfFunctionDefinitions" },
  { type: "UnitDefinition", label: "Unit definition", plural: "Unit definitions", color: "#f1b6da", icon: "pi-calculator", pkg: "core", listKey: "listOfUnitDefinitions" },
  { type: "Compartment", label: "Compartment", plural: "Compartments", color: "#92c5de", icon: "pi-box", pkg: "core", listKey: "listOfCompartments" },
  { type: "Species", label: "Species", plural: "Species", color: "#abdda4", icon: "pi-circle", pkg: "core", listKey: "listOfSpecies" },
  { type: "Parameter", label: "Parameter", plural: "Parameters", color: "#fdae61", icon: "pi-sliders-h", pkg: "core", listKey: "listOfParameters" },
  { type: "InitialAssignment", label: "Initial assignment", plural: "Initial assignments", color: "#fee08b", icon: "pi-arrow-circle-left", pkg: "core", listKey: "listOfInitialAssignments" },
  { type: "AssignmentRule", label: "Assignment rule", plural: "Assignment rules", color: "#fb9a99", icon: "pi-equals", pkg: "core", listKey: "listOfRules" },
  { type: "RateRule", label: "Rate rule", plural: "Rate rules", color: "#fb9a99", icon: "pi-wave-pulse", pkg: "core", listKey: "listOfRules" },
  { type: "AlgebraicRule", label: "Algebraic rule", plural: "Algebraic rules", color: "#fb9a99", icon: "pi-hashtag", pkg: "core", listKey: "listOfRules" },
  { type: "Constraint", label: "Constraint", plural: "Constraints", color: "#fdae61", icon: "pi-lock", pkg: "core", listKey: "listOfConstraints" },
  { type: "Reaction", label: "Reaction", plural: "Reactions", color: "#a6cee3", icon: "pi-arrow-right-arrow-left", pkg: "core", listKey: "listOfReactions" },
  { type: "Event", label: "Event", plural: "Events", color: "#fed08b", icon: "pi-clock", pkg: "core", listKey: "listOfEvents" },
  { type: "Submodel", label: "Submodel", plural: "Submodels", color: "#00ccff", icon: "pi-th-large", pkg: "comp", listKey: "listOfSubmodels" },
  { type: "Port", label: "Port", plural: "Ports", color: "#fed9a6", icon: "pi-sign-in", pkg: "comp", listKey: "listOfPorts" },
  { type: "GeneProduct", label: "Gene product", plural: "Gene products", color: "#d53e4f", icon: "pi-tag", pkg: "fbc", listKey: "listOfGeneProducts" },
  { type: "Objective", label: "Objective", plural: "Objectives", color: "#f46d43", icon: "pi-bullseye", pkg: "fbc", listKey: "listOfObjectives" },
];

export const NESTED_TYPES: readonly SbmlTypeInfo<NestedElementType>[] = [
  { type: "SpeciesReference", label: "Species reference", plural: "Species references", color: "#abdda4", icon: "pi-circle-fill", pkg: "core" },
  { type: "ModifierSpeciesReference", label: "Modifier species reference", plural: "Modifier species references", color: "#abdda4", icon: "pi-circle", pkg: "core" },
  { type: "KineticLaw", label: "Kinetic law", plural: "Kinetic laws", color: "#a6cee3", icon: "pi-calculator", pkg: "core" },
  { type: "LocalParameter", label: "Local parameter", plural: "Local parameters", color: "#fdae61", icon: "pi-sliders-h", pkg: "core" },
  { type: "EventAssignment", label: "Event assignment", plural: "Event assignments", color: "#fed08b", icon: "pi-equals", pkg: "core" },
  { type: "Uncertainty", label: "Uncertainty", plural: "Uncertainties", color: "#c7c7c7", icon: "pi-question-circle", pkg: "distrib" },
];

export const SBML_TYPES: Readonly<Record<SbmlType, SbmlTypeInfo>> = Object.fromEntries(
  [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES].map((info) => [info.type, info]),
) as Record<SbmlType, SbmlTypeInfo>;

export function typeInfo(type: SbmlType): SbmlTypeInfo {
  return SBML_TYPES[type];
}

const ELEMENT_TYPE_SET = new Set<string>(ELEMENT_TYPES.map((info) => info.type));

export function isElementType(type: string): type is ElementType {
  return ELEMENT_TYPE_SET.has(type);
}
```

`frontend/src/data/edgeKinds.ts`:
```ts
import type { EdgeKind } from "@/api/types";

/** The fixed order of the link groups in the inspector. */
export const EDGE_KINDS: readonly EdgeKind[] = [
  "compartment",
  "reactant",
  "product",
  "modifier",
  "variable",
  "symbol",
  "units",
  "conversionFactor",
  "fluxBound",
  "geneProduct",
  "associatedSpecies",
  "fluxObjective",
  "modelRef",
  "port",
  "replacedBy",
  "replacedElement",
  "math",
];

const LABELS: Readonly<Record<EdgeKind, string>> = {
  compartment: "compartment",
  reactant: "reactant",
  product: "product",
  modifier: "modifier",
  variable: "variable",
  symbol: "symbol",
  units: "units",
  conversionFactor: "conversion factor",
  fluxBound: "flux bound",
  geneProduct: "gene product",
  associatedSpecies: "associated species",
  fluxObjective: "flux objective",
  modelRef: "model reference",
  port: "port",
  replacedBy: "replaced by",
  replacedElement: "replaced element",
  math: "math",
};

export function edgeKindLabel(kind: EdgeKind): string {
  return LABELS[kind];
}
```

- [ ] **Step 6: Run the test and the checks**

```bash
npx vitest run tests/unit/sbmlTypes.test.ts   # PASS
npm run format && npm run lint && npm run typecheck
```

If `typecheck` complains that `EDGE_KINDS` misses a kind, the schema has changed: rerun `npm run types` and extend the list.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/types/report.ts frontend/src/api/types.ts frontend/src/data frontend/tests/unit/sbmlTypes.test.ts
git commit -m "Generate the report types and describe the SBML types"
```

---

### Task 3: Api client with the error contract and recorded fixtures

**Files:**
- Create: `frontend/src/api/client.ts`, `frontend/scripts/fixtures.mjs`, `frontend/tests/fixtures/*.json`, `frontend/tests/unit/fixtures.ts`
- Test: `frontend/tests/unit/client.test.ts`

**Interfaces:**
- Consumes: `ReportResponse`, `ExampleMetaData`, `AnnotationInfo` from `@/api/types`.
- Produces: `class ApiError extends Error { traceback: string | null; warnings: string[] }`, `toApiError(error: unknown): ApiError`, `getExamples(): Promise<ExampleMetaData[]>`, `getExample(id: string): Promise<ReportResponse>`, `getUrl(url: string): Promise<ReportResponse>`, `postFile(file: File): Promise<ReportResponse>`, `postContent(text: string): Promise<ReportResponse>`, `getAnnotationResource(resource: string): Promise<AnnotationInfo>`; the fixtures `repressilator`, `icg_body`, `fbc_example`, `model_definitions`, `comp_models`, `distrib_uncertainties`, `examples` and `loadFixture(name): ReportResponse`, `loadExamplesFixture(): ExampleMetaData[]`.

- [ ] **Step 1: Write the failing client test**

`frontend/tests/unit/client.test.ts`:
```ts
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getAnnotationResource,
  getExample,
  getExamples,
  postContent,
  postFile,
} from "@/api/client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("requests the examples from the api url", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ examples: [{ id: "a" }] }));
    vi.stubGlobal("fetch", fetchMock);
    const examples = await getExamples();
    expect(examples).toEqual([{ id: "a" }]);
    expect(fetchMock).toHaveBeenCalledWith(
      `${import.meta.env.VITE_API_URL}/examples`,
      expect.anything(),
    );
  });

  it("encodes the example id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ uid: "x", manifest: {}, reports: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await getExample("icg_body (icg_body.xml)");
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      `${import.meta.env.VITE_API_URL}/examples/icg_body%20(icg_body.xml)`,
    );
  });

  it("throws ApiError for the error contract", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ errors: ["example for id does not exist 'x'", "Traceback ..."], warnings: [], info: {} }),
      ),
    );
    const error = await getExample("x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toBe("example for id does not exist 'x'");
    expect((error as ApiError).traceback).toBe("Traceback ...");
  });

  it("throws ApiError when the backend is not reachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const error = await getExamples().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toMatch(/not reachable/);
  });

  it("throws ApiError for a non JSON body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>", { status: 502 })));
    const error = await getExamples().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toMatch(/502/);
  });

  it("posts the file as multipart field source", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ uid: "x", manifest: {}, reports: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await postFile(new File(["<sbml/>"], "model.xml"));
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect((init.body as FormData).get("source")).toBeInstanceOf(File);
  });

  it("posts the content as raw body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ uid: "x", manifest: {}, reports: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await postContent("<sbml/>");
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(init.body).toBe("<sbml/>");
  });

  it("returns the annotation info although it carries an errors list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ resource: "https://identifiers.org/chebi/CHEBI:15377", label: "water", errors: ["no ols"], warnings: [] }),
      ),
    );
    const info = await getAnnotationResource("https://identifiers.org/chebi/CHEBI:15377");
    expect(info.label).toBe("water");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/client.test.ts`
Expected: FAIL, cannot resolve `@/api/client`.

- [ ] **Step 3: Write the client**

`frontend/src/api/client.ts`:
```ts
import type { AnnotationInfo, ExampleMetaData, ReportResponse } from "@/api/types";

const API_URL: string = import.meta.env.VITE_API_URL;

/** A failure reported by the backend or a failure to reach it. */
export class ApiError extends Error {
  readonly traceback: string | null;
  readonly warnings: string[];

  constructor(message: string, traceback: string | null = null, warnings: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.traceback = traceback;
    this.warnings = warnings;
  }
}

/** Wrap an unknown thrown value into an ApiError. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (error instanceof Error) return new ApiError(error.message, error.stack ?? null);
  return new ApiError(String(error));
}

interface ErrorBody {
  errors: string[];
  warnings: string[];
  info: Record<string, string>;
}

/** The error contract: status 200 with a non-empty errors list and the info of the request. */
function isErrorBody(body: unknown): body is ErrorBody {
  if (typeof body !== "object" || body === null) return false;
  const candidate = body as Partial<ErrorBody>;
  return (
    Array.isArray(candidate.errors) &&
    candidate.errors.length > 0 &&
    typeof candidate.info === "object" &&
    candidate.info !== null
  );
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    throw new ApiError(
      `The backend at ${API_URL} is not reachable`,
      error instanceof Error ? error.message : null,
    );
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ApiError(`The backend answered with status ${response.status} and no JSON body`);
  }
  if (isErrorBody(body)) {
    throw new ApiError(body.errors[0] ?? "Unknown error", body.errors[1] ?? null, body.warnings);
  }
  if (!response.ok) {
    throw new ApiError(`The backend answered with status ${response.status}`);
  }
  return body as T;
}

export async function getExamples(): Promise<ExampleMetaData[]> {
  const body = await request<{ examples: ExampleMetaData[] }>("/examples");
  return body.examples;
}

export function getExample(id: string): Promise<ReportResponse> {
  return request<ReportResponse>(`/examples/${encodeURIComponent(id)}`);
}

export function getUrl(url: string): Promise<ReportResponse> {
  return request<ReportResponse>(`/url?url=${encodeURIComponent(url)}`);
}

export function postFile(file: File): Promise<ReportResponse> {
  const form = new FormData();
  form.append("source", file, file.name);
  return request<ReportResponse>("/file", { method: "POST", body: form });
}

export function postContent(text: string): Promise<ReportResponse> {
  return request<ReportResponse>("/content", {
    method: "POST",
    body: text,
    headers: { "Content-Type": "application/xml" },
  });
}

export function getAnnotationResource(resource: string): Promise<AnnotationInfo> {
  return request<AnnotationInfo>(`/annotation_resource?resource=${encodeURIComponent(resource)}`);
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npx vitest run tests/unit/client.test.ts`
Expected: PASS (8 tests). Vitest loads `.env.development`, so `import.meta.env.VITE_API_URL` is `http://localhost:1444/api`.

- [ ] **Step 5: Write the fixtures script**

`frontend/scripts/fixtures.mjs`:
```js
// Record the api responses of a few examples for the unit tests.
// Usage: start the backend (uv run uvicorn sbml4humans.api:api --port 1444), then `npm run fixtures`.
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const API_URL = process.env.VITE_API_URL ?? "http://localhost:1444/api";
const FIXTURES_DIR = fileURLToPath(new URL("../tests/fixtures/", import.meta.url));

/** fixture name -> example id */
const EXAMPLES = {
  repressilator: "BIOMD0000000012",
  icg_body: "icg_body (icg_body.xml)",
  fbc_example: "fbc_example (fbc_example.xml)",
  model_definitions: "model_definitions (model_definitions.xml)",
  comp_models: "CompModels",
  distrib_uncertainties: "distrib_uncertainties (distrib_uncertainties.xml)",
};

async function fetchJson(path) {
  const response = await fetch(`${API_URL}${path}`);
  const body = await response.json();
  if (Array.isArray(body.errors) && body.errors.length > 0) {
    throw new Error(`${path}: ${body.errors[0]}`);
  }
  return body;
}

await mkdir(FIXTURES_DIR, { recursive: true });
const examples = await fetchJson("/examples");
await writeFile(`${FIXTURES_DIR}examples.json`, JSON.stringify(examples.examples, null, 2));
console.log(`examples.json: ${examples.examples.length} examples`);

for (const [name, id] of Object.entries(EXAMPLES)) {
  const report = await fetchJson(`/examples/${encodeURIComponent(id)}`);
  await writeFile(`${FIXTURES_DIR}${name}.json`, JSON.stringify(report, null, 2));
  console.log(`${name}.json: ${Object.keys(report.reports).join(", ")}`);
}
```

- [ ] **Step 6: Record the fixtures**

Start the backend in a second terminal and record:
```bash
(cd /home/mkoenig/git/sbml4humans/backend && uv run uvicorn sbml4humans.api:api --port 1444) &
sleep 5
cd /home/mkoenig/git/sbml4humans/frontend && npm run fixtures
ls -la tests/fixtures && du -sh tests/fixtures
```

Expected: seven files; `comp_models.json` has three entries (`./models/omex_comp_flat.xml`, `./models/omex_minimal.xml`, `./models/omex_comp.xml`, no master), `icg_body.json` one external model definition, `model_definitions.json` two models (`model_definitions` of kind `model`, `m1` of kind `modelDefinition`). The directory is a few MB.

- [ ] **Step 7: Write the fixture loader**

`frontend/tests/unit/fixtures.ts`:
```ts
import { readFileSync } from "node:fs";

import type { ExampleMetaData, Report, ReportResponse } from "@/api/types";

export type FixtureName =
  | "repressilator"
  | "icg_body"
  | "fbc_example"
  | "model_definitions"
  | "comp_models"
  | "distrib_uncertainties";

export function loadFixture(name: FixtureName): ReportResponse {
  const path = new URL(`../fixtures/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(path, "utf8")) as ReportResponse;
}

/** The report of the first (or given) entry of a fixture. */
export function loadReport(name: FixtureName, location?: string): Report {
  const response = loadFixture(name);
  const key = location ?? Object.keys(response.reports)[0];
  const entry = key === undefined ? undefined : response.reports[key];
  if (!entry) throw new Error(`fixture ${name} has no entry ${location}`);
  return entry.report;
}

export function loadExamplesFixture(): ExampleMetaData[] {
  const path = new URL("../fixtures/examples.json", import.meta.url);
  return JSON.parse(readFileSync(path, "utf8")) as ExampleMetaData[];
}
```

Add to `tests/unit/client.test.ts` a last test that the recorded fixture validates the shape the client returns:
```ts
import { loadFixture } from "./fixtures";

it("fixtures carry the report response shape", () => {
  const response = loadFixture("repressilator");
  expect(response.manifest.entries.some((entry) => entry.master)).toBe(true);
  const report = response.reports["./model.xml"]?.report;
  expect(report?.document.sbmlType).toBe("SBMLDocument");
  expect(report?.models[0]?.id).toBe("BIOMD0000000012");
  expect(report?.linkGraph.edges.length).toBeGreaterThan(0);
});
```

- [ ] **Step 8: Run all checks**

```bash
npm run test:unit && npm run format && npm run lint && npm run typecheck
```

Expected: PASS. Prettier ignores `tests/fixtures/*.json`? No: add `tests/fixtures/` to `.prettierignore` (the files are large and generated).

- [ ] **Step 9: Commit**

```bash
git add frontend/src/api/client.ts frontend/scripts frontend/tests frontend/.prettierignore
git commit -m "Add the api client with the error contract and record the fixtures"
```

---

### Task 4: ReportIndex and search

**Files:**
- Create: `frontend/src/report/index.ts`, `frontend/src/report/search.ts`
- Test: `frontend/tests/unit/reportIndex.test.ts`, `frontend/tests/unit/search.test.ts`

**Interfaces:**
- Consumes: the fixtures of Task 3, `ELEMENT_TYPES` of Task 2.
- Produces:
  ```ts
  class ReportIndex {
    constructor(report: Report)
    readonly report: Report
    readonly elements: ReadonlyMap<string, SBase>
    readonly nodes: ReadonlyMap<string, Node>
    get document(): SBMLDocument
    get models(): Model[]
    get externalModelDefinitions(): ExternalModelDefinition[]
    get mainModel(): Model | null            // kind "model", else the first model
    model(id: string): Model | null
    get(pk: string): SBase | undefined
    has(pk: string): boolean
    byType(modelId: string): ReadonlyMap<ElementType, SbmlElement[]>   // list order, every type present (maybe empty)
    modelOf(pk: string): string | null       // node.model
    references(pk: string): Edge[]           // outgoing
    referencedBy(pk: string): Edge[]         // incoming
    resolve(sourcePk: string, kind: EdgeKind, id: string): string | null
  }
  ```
  Edge sources of the backend link graph (`backend/sbml4humans/links.py`): species -> compartment, units, conversionFactor; compartment, parameter, local parameter -> units; model -> units, conversionFactor; reaction -> compartment, reactant, product, modifier, fluxBound, geneProduct; rule and event assignment -> variable; initial assignment -> symbol; submodel -> modelRef (target: the model or external model definition); port -> port (idRef, unitRef, metaIdRef); gene product -> associatedSpecies; objective -> fluxObjective (target: the reaction); any element -> replacedBy, replacedElement (target: the submodel); element, kinetic law or uncertainty -> math (target: the symbols).
  ```ts
  function matches(element: SBase, query: string): boolean
  function normalizeQuery(query: string): string
  ```

- [ ] **Step 1: Write the failing index test**

`frontend/tests/unit/reportIndex.test.ts`:
```ts
import { describe, expect, it } from "vitest";

import type { Reaction, Species } from "@/api/types";
import { ReportIndex } from "@/report/index";

import { loadReport } from "./fixtures";

const repressilator = new ReportIndex(loadReport("repressilator"));
const icgBody = new ReportIndex(loadReport("icg_body"));
const definitions = new ReportIndex(loadReport("model_definitions"));
const distrib = new ReportIndex(loadReport("distrib_uncertainties"));

describe("ReportIndex", () => {
  it("indexes the document, the models and every element by pk", () => {
    expect(repressilator.get(repressilator.document.pk)?.sbmlType).toBe("SBMLDocument");
    const model = repressilator.mainModel;
    expect(model?.id).toBe("BIOMD0000000012");
    expect(repressilator.get(model!.pk)).toBe(model);
    for (const species of model!.listOfSpecies) {
      expect(repressilator.get(species.pk)).toBe(species);
    }
  });

  it("indexes the nested elements", () => {
    const reaction = repressilator.mainModel!.listOfReactions.find(
      (r) => r.listOfReactants.length > 0 && r.kineticLaw,
    )!;
    const reactant = reaction.listOfReactants[0]!;
    expect(repressilator.get(reactant.pk)).toBe(reactant);
    expect(repressilator.get(reaction.kineticLaw!.pk)).toBe(reaction.kineticLaw);
    for (const parameter of reaction.kineticLaw!.listOfLocalParameters) {
      expect(repressilator.get(parameter.pk)).toBe(parameter);
    }
    const uncertainty = distrib.elements.values().find((e) => e.sbmlType === "Uncertainty");
    expect(uncertainty).toBeDefined();
  });

  it("indexes the external model definitions", () => {
    expect(icgBody.externalModelDefinitions).toHaveLength(1);
    const emd = icgBody.externalModelDefinitions[0]!;
    expect(icgBody.get(emd.pk)).toBe(emd);
  });

  it("groups the elements of a model by type in list order", () => {
    const byType = repressilator.byType("BIOMD0000000012");
    expect([...byType.keys()]).toHaveLength(16);
    expect(byType.get("Species")).toEqual(repressilator.mainModel!.listOfSpecies);
    expect(byType.get("Submodel")).toEqual([]);
    const rules = definitions.byType("model_definitions");
    expect(rules.get("AssignmentRule")!.every((r) => r.sbmlType === "AssignmentRule")).toBe(true);
  });

  it("knows the main model and the model definitions", () => {
    expect(definitions.models.map((m) => m.kind)).toEqual(["model", "modelDefinition"]);
    expect(definitions.mainModel?.id).toBe("model_definitions");
    expect(definitions.model("m1")?.kind).toBe("modelDefinition");
    expect(definitions.model("nope")).toBeNull();
  });

  it("indexes the edges in both directions", () => {
    const species = repressilator.mainModel!.listOfSpecies[0]!;
    const compartmentEdge = repressilator.references(species.pk).find((e) => e.kind === "compartment");
    expect(compartmentEdge).toBeDefined();
    const compartment = repressilator.get(compartmentEdge!.target)!;
    expect(compartment.sbmlType).toBe("Compartment");
    expect(repressilator.referencedBy(compartment.pk)).toContainEqual(compartmentEdge);
    expect(repressilator.referencedBy("nope")).toEqual([]);
  });

  it("resolves a reference by edge kind and id", () => {
    const species = repressilator.mainModel!.listOfSpecies[0] as Species;
    const pk = repressilator.resolve(species.pk, "compartment", species.compartment);
    expect(pk).not.toBeNull();
    expect(repressilator.get(pk!)?.id).toBe(species.compartment);
    expect(repressilator.resolve(species.pk, "compartment", "nope")).toBeNull();
    expect(repressilator.resolve(species.pk, "units", "litre")).toBeNull();
  });

  it("resolves the species of a reactant from the reaction", () => {
    // the reactant, product and modifier edges start at the reaction, not at the species reference
    const reaction = repressilator.mainModel!.listOfReactions.find(
      (r) => r.listOfReactants.length > 0,
    ) as Reaction;
    const reactant = reaction.listOfReactants[0]!;
    const pk = repressilator.resolve(reaction.pk, "reactant", reactant.species);
    expect(repressilator.get(pk!)?.sbmlType).toBe("Species");
    expect(repressilator.resolve(reactant.pk, "reactant", reactant.species)).toBeNull();
  });

  it("tells the model of an element", () => {
    const species = repressilator.mainModel!.listOfSpecies[0]!;
    expect(repressilator.modelOf(species.pk)).toBe("BIOMD0000000012");
    expect(repressilator.modelOf("nope")).toBeNull();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/reportIndex.test.ts`
Expected: FAIL, cannot resolve `@/report/index`.

- [ ] **Step 3: Write the index**

`frontend/src/report/index.ts`:
```ts
import type {
  Edge,
  EdgeKind,
  SbmlElement,
  ElementType,
  ExternalModelDefinition,
  Model,
  Node,
  Report,
  SBMLDocument,
  SBase,
} from "@/api/types";
import { ELEMENT_TYPES } from "@/data/sbmlTypes";

function push<K, V>(map: Map<K, V[]>, key: K, value: V): void {
  const list = map.get(key);
  if (list) list.push(value);
  else map.set(key, [value]);
}

/** Lookups over one report: every element by pk, the elements of a model by type, the edges in both directions. */
export class ReportIndex {
  readonly report: Report;
  readonly elements = new Map<string, SBase>();
  readonly nodes = new Map<string, Node>();
  private readonly outgoing = new Map<string, Edge[]>();
  private readonly incoming = new Map<string, Edge[]>();
  private readonly byModel = new Map<string, Map<ElementType, SbmlElement[]>>();

  constructor(report: Report) {
    this.report = report;
    this.add(report.document);
    for (const definition of report.externalModelDefinitions) this.add(definition);
    for (const model of report.models) this.addModel(model);
    for (const node of report.linkGraph.nodes) this.nodes.set(node.pk, node);
    for (const edge of report.linkGraph.edges) {
      push(this.outgoing, edge.source, edge);
      push(this.incoming, edge.target, edge);
    }
  }

  get document(): SBMLDocument {
    return this.report.document;
  }

  get models(): Model[] {
    return this.report.models;
  }

  get externalModelDefinitions(): ExternalModelDefinition[] {
    return this.report.externalModelDefinitions;
  }

  /** The model of kind "model", else the first model definition. */
  get mainModel(): Model | null {
    return this.models.find((model) => model.kind === "model") ?? this.models[0] ?? null;
  }

  model(id: string): Model | null {
    return this.models.find((model) => model.id === id) ?? null;
  }

  get(pk: string): SBase | undefined {
    return this.elements.get(pk);
  }

  has(pk: string): boolean {
    return this.elements.has(pk);
  }

  /** The elements of the model grouped by type, every element type present, in list order. */
  byType(modelId: string): ReadonlyMap<ElementType, SbmlElement[]> {
    return this.byModel.get(modelId) ?? new Map();
  }

  modelOf(pk: string): string | null {
    return this.nodes.get(pk)?.model ?? null;
  }

  /** The edges from the element to the elements it references. */
  references(pk: string): Edge[] {
    return this.outgoing.get(pk) ?? [];
  }

  /** The edges from the elements referencing the element. */
  referencedBy(pk: string): Edge[] {
    return this.incoming.get(pk) ?? [];
  }

  /** The pk of the element with the id referenced by the source through an edge of the kind, if any. */
  resolve(sourcePk: string, kind: EdgeKind, id: string | null | undefined): string | null {
    if (!id) return null;
    for (const edge of this.references(sourcePk)) {
      if (edge.kind !== kind) continue;
      const target = this.nodes.get(edge.target);
      if (target?.id === id || this.elements.get(edge.target)?.id === id) return edge.target;
    }
    return null;
  }

  private add(element: SBase): void {
    this.elements.set(element.pk, element);
    for (const uncertainty of element.uncertainties ?? []) this.add(uncertainty);
  }

  private addModel(model: Model): void {
    this.add(model);
    const byType = new Map<ElementType, SbmlElement[]>();
    for (const info of ELEMENT_TYPES) {
      const list = (model[info.listKey] ?? []) as SbmlElement[];
      byType.set(
        info.type,
        list.filter((element) => element.sbmlType === info.type),
      );
    }
    for (const elements of byType.values()) {
      for (const element of elements) this.addElement(element);
    }
    if (model.id) this.byModel.set(model.id, byType);
  }

  private addElement(element: SbmlElement): void {
    this.add(element);
    switch (element.sbmlType) {
      case "Reaction":
        for (const reference of element.listOfReactants ?? []) this.add(reference);
        for (const reference of element.listOfProducts ?? []) this.add(reference);
        for (const reference of element.listOfModifiers ?? []) this.add(reference);
        if (element.kineticLaw) {
          this.add(element.kineticLaw);
          for (const parameter of element.kineticLaw.listOfLocalParameters ?? []) this.add(parameter);
        }
        break;
      case "Event":
        for (const assignment of element.listOfEventAssignments ?? []) this.add(assignment);
        break;
      default:
        break;
    }
  }
}
```

- [ ] **Step 4: Run the index test**

Run: `npx vitest run tests/unit/reportIndex.test.ts`
Expected: PASS. If `byType` with 16 keys fails because the rules are split into three list keys, that is expected and handled by the `sbmlType` filter; if a nested element is missing, check the fixture has it (the repressilator has kinetic laws with local parameters).

- [ ] **Step 5: Write the failing search test**

`frontend/tests/unit/search.test.ts`:
```ts
import { describe, expect, it } from "vitest";

import type { Species } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { matches, normalizeQuery } from "@/report/search";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const model = index.mainModel!;

describe("search", () => {
  it("normalizes the query", () => {
    expect(normalizeQuery("  LacI ")).toBe("laci");
  });

  it("matches everything for the empty query", () => {
    expect(matches(model.listOfSpecies[0]!, "")).toBe(true);
    expect(matches(model.listOfSpecies[0]!, "   ")).toBe(true);
  });

  it("matches id, name and metaId case insensitively", () => {
    const species = model.listOfSpecies.find((s) => s.name)!;
    expect(matches(species, species.id!.toUpperCase())).toBe(true);
    expect(matches(species, species.name!.slice(0, 4).toLowerCase())).toBe(true);
    if (species.metaId) expect(matches(species, species.metaId)).toBe(true);
    expect(matches(species, "definitely-not-there")).toBe(false);
  });

  it("matches the sbo term", () => {
    const withSbo = [...index.elements.values()].find((e) => e.sbo);
    if (withSbo) expect(matches(withSbo, withSbo.sbo!)).toBe(true);
  });

  it("matches the formula of the math and the equation of a reaction", () => {
    const reaction = model.listOfReactions.find((r) => r.kineticLaw?.math)!;
    const symbol = reaction.kineticLaw!.math!.formula.match(/[A-Za-z_]\w*/)![0];
    expect(matches(reaction, symbol)).toBe(true);
    const reactant = reaction.equation.split(/\s|->|=>|<=>/).find((t) => t && !/^\d+$/.test(t))!;
    expect(matches(reaction, reactant)).toBe(true);
  });

  it("matches the text of the notes without the html tags", () => {
    const withNotes = [...index.elements.values()].find((e) => e.notes && /<p>/.test(e.notes))!;
    const text = withNotes.notes!.replace(/<[^>]+>/g, " ").trim().split(/\s+/)[0]!;
    expect(matches(withNotes, text)).toBe(true);
    expect(matches(withNotes, "<p>")).toBe(false);
  });

  it("does not match a species by the compartment id", () => {
    const species = model.listOfSpecies[0] as Species;
    if (!species.id!.includes(species.compartment)) {
      expect(matches(species, species.compartment)).toBe(false);
    }
  });
});
```

- [ ] **Step 6: Run the test to verify it fails**

Run: `npx vitest run tests/unit/search.test.ts`
Expected: FAIL, cannot resolve `@/report/search`.

- [ ] **Step 7: Write the search**

`frontend/src/report/search.ts`:
```ts
import type { Math, SBase } from "@/api/types";

const texts = new WeakMap<SBase, string>();

export function normalizeQuery(query: string): string {
  return query.trim().toLowerCase();
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, " ");
}

function* maths(element: SBase): Generator<Math | null | undefined> {
  if ("math" in element) yield element.math;
  if (element.sbmlType === "Reaction") yield element.kineticLaw?.math;
  if (element.sbmlType === "Event") {
    yield element.trigger?.math;
    yield element.priority;
    yield element.delay;
    for (const assignment of element.listOfEventAssignments ?? []) yield assignment.math;
  }
  if (element.sbmlType === "Uncertainty") {
    for (const parameter of element.uncertParameters ?? []) yield parameter.math;
  }
}

/** The searchable text of an element: id, name, metaId, sbo, notes text, formulas and equation. */
function searchText(element: SBase): string {
  const cached = texts.get(element);
  if (cached !== undefined) return cached;
  const parts: (string | null | undefined)[] = [element.id, element.name, element.metaId, element.sbo];
  if (element.notes) parts.push(stripHtml(element.notes));
  for (const math of maths(element)) parts.push(math?.formula);
  if (element.sbmlType === "Reaction") parts.push(element.equation);
  const text = parts.filter((part): part is string => !!part).join("\n").toLowerCase();
  texts.set(element, text);
  return text;
}

/** Case insensitive substring match of the query against the searchable text. */
export function matches(element: SBase, query: string): boolean {
  const normalized = normalizeQuery(query);
  return normalized === "" || searchText(element).includes(normalized);
}
```

- [ ] **Step 8: Run all checks**

```bash
npm run test:unit && npm run format && npm run lint && npm run typecheck
```

Expected: PASS. A `noUncheckedIndexedAccess` complaint in the tests is silenced with `!` after the index access, as the tests above do.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/report frontend/tests/unit/reportIndex.test.ts frontend/tests/unit/search.test.ts
git commit -m "Index the report by pk and edge and add the search"
```

---

### Task 5: View state, stores, router and page skeletons

**Files:**
- Create: `frontend/src/report/query.ts`, `frontend/src/report/view.ts`, `frontend/src/report/context.ts`, `frontend/src/stores/report.ts`, `frontend/src/stores/examples.ts`, `frontend/src/router.ts`, `frontend/src/pages/HomePage.vue`, `frontend/src/pages/ExamplesPage.vue`, `frontend/src/pages/ReportPage.vue`, `frontend/src/components/layout/AppBar.vue`, `frontend/src/components/layout/LoadingState.vue`, `frontend/src/components/layout/ErrorState.vue`
- Modify: `frontend/src/main.ts`, `frontend/src/App.vue`
- Test: `frontend/tests/unit/query.test.ts`, `frontend/tests/unit/reportStore.test.ts`

**Interfaces:**
- Consumes: the client of Task 3, `ReportIndex` of Task 4, `isElementType` of Task 2.
- Produces:
  ```ts
  interface ViewState { entry: string | null; model: string | null; pk: string | null; q: string; types: ElementType[] | null }
  function parseQuery(query: LocationQuery): ViewState
  function toQuery(state: ViewState): LocationQueryRaw          // omits defaults
  function useReportView(): { state: ComputedRef<ViewState>; select(pk: string | null, mode?: "push" | "replace"): Promise<unknown>; setSearch(q: string): Promise<unknown>; setTypes(types: ElementType[] | null): Promise<unknown>; setEntry(entry: string | null): Promise<unknown>; setModel(model: string | null): Promise<unknown>; routeFor(pk: string): RouteLocationRaw }
  const ReportIndexKey: InjectionKey<Ref<ReportIndex | null>>; function useReportIndex(): Ref<ReportIndex | null>
  type SourceKind = "example" | "url" | "file" | "content"; interface ReportSource { kind: SourceKind; id?: string; url?: string; name: string }
  useReportStore(): { response, source, loading, error, entries, defaultEntry, indexFor(location), loadExample(id), loadUrl(url), loadFile(file), loadContent(text), clear() }
  useExamplesStore(): { examples, loading, error, loadExamples() }
  routes: "home" (/), "examples" (/examples), "example" (/examples/:id), "report" (/report)
  ```
  Components: `AppBar` (slots `context`, `actions`), `LoadingState {message: string}`, `ErrorState {error: ApiError}` with `data-testid="error-state"`, `error-message`, `error-traceback-toggle`.

- [ ] **Step 1: Write the failing query test**

`frontend/tests/unit/query.test.ts`:
```ts
import { describe, expect, it } from "vitest";

import { parseQuery, toQuery } from "@/report/query";

describe("view state query", () => {
  it("parses an empty query into the defaults", () => {
    expect(parseQuery({})).toEqual({ entry: null, model: null, pk: null, q: "", types: null });
  });

  it("parses every parameter", () => {
    expect(
      parseQuery({ entry: "./model.xml", model: "m1", pk: "m1/Species:s1", q: "laci", types: "Species,Reaction" }),
    ).toEqual({
      entry: "./model.xml",
      model: "m1",
      pk: "m1/Species:s1",
      q: "laci",
      types: ["Species", "Reaction"],
    });
  });

  it("drops unknown types and takes the first of repeated parameters", () => {
    expect(parseQuery({ types: "Species,Nope", pk: ["a", "b"] })).toMatchObject({
      types: ["Species"],
      pk: "a",
    });
    expect(parseQuery({ types: "Nope" }).types).toEqual([]);
  });

  it("writes only the non default values", () => {
    expect(toQuery({ entry: null, model: null, pk: null, q: "", types: null })).toEqual({});
    expect(toQuery({ entry: "./m.xml", model: "m", pk: "p", q: "x", types: ["Species"] })).toEqual({
      entry: "./m.xml",
      model: "m",
      pk: "p",
      q: "x",
      types: "Species",
    });
  });

  it("round trips", () => {
    const state = { entry: "./a b.xml", model: "m", pk: "m/Species:s 1", q: "a&b", types: ["Species" as const] };
    expect(parseQuery(toQuery(state) as Record<string, string>)).toEqual(state);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/query.test.ts`
Expected: FAIL, cannot resolve `@/report/query`.

- [ ] **Step 3: Write query.ts**

`frontend/src/report/query.ts`:
```ts
import type { LocationQuery, LocationQueryRaw, LocationQueryValue } from "vue-router";

import type { ElementType } from "@/api/types";
import { isElementType } from "@/data/sbmlTypes";

/** The view state of the report page, kept in the route query. */
export interface ViewState {
  /** Manifest location of the SBML entry, null = master or first entry. */
  entry: string | null;
  /** Id of the model or model definition, null = main model. */
  model: string | null;
  /** Selected element, null = inspector closed. */
  pk: string | null;
  /** Search text. */
  q: string;
  /** Visible element types, null = all. */
  types: ElementType[] | null;
}

function first(value: LocationQueryValue | LocationQueryValue[] | undefined): string | null {
  const single = Array.isArray(value) ? value[0] : value;
  return single ? single : null;
}

export function parseQuery(query: LocationQuery): ViewState {
  const types = first(query.types);
  return {
    entry: first(query.entry),
    model: first(query.model),
    pk: first(query.pk),
    q: first(query.q) ?? "",
    types: types === null ? null : types.split(",").filter(isElementType),
  };
}

export function toQuery(state: ViewState): LocationQueryRaw {
  const query: LocationQueryRaw = {};
  if (state.entry) query.entry = state.entry;
  if (state.model) query.model = state.model;
  if (state.pk) query.pk = state.pk;
  if (state.q) query.q = state.q;
  if (state.types !== null) query.types = state.types.join(",");
  return query;
}
```

- [ ] **Step 4: Run the query test**

Run: `npx vitest run tests/unit/query.test.ts`
Expected: PASS.

- [ ] **Step 5: Write view.ts and context.ts**

`frontend/src/report/view.ts`:
```ts
import { computed, type ComputedRef } from "vue";
import { useRoute, useRouter, type RouteLocationRaw } from "vue-router";

import type { ElementType } from "@/api/types";
import { parseQuery, toQuery, type ViewState } from "@/report/query";

type Mode = "push" | "replace";

/** The view state of the report page and the actions that write it back to the route. */
export function useReportView(): {
  state: ComputedRef<ViewState>;
  select(pk: string | null, mode?: Mode): Promise<unknown>;
  setSearch(q: string): Promise<unknown>;
  setTypes(types: ElementType[] | null): Promise<unknown>;
  setEntry(entry: string | null): Promise<unknown>;
  setModel(model: string | null): Promise<unknown>;
  routeFor(pk: string): RouteLocationRaw;
} {
  const route = useRoute();
  const router = useRouter();
  const state = computed(() => parseQuery(route.query));

  function update(patch: Partial<ViewState>, mode: Mode = "push"): Promise<unknown> {
    const query = { ...toQuery({ ...state.value, ...patch }) };
    // the url of a loaded report is not view state, keep it
    if (typeof route.query.url === "string") query.url = route.query.url;
    return router[mode]({ path: route.path, query });
  }

  return {
    state,
    select: (pk, mode = "push") => update({ pk }, mode),
    setSearch: (q) => update({ q }, "replace"),
    setTypes: (types) => update({ types }),
    setEntry: (entry) => update({ entry, model: null, pk: null }),
    setModel: (model) => update({ model, pk: null }),
    routeFor: (pk) => {
      const query = { ...toQuery({ ...state.value, pk }) };
      if (typeof route.query.url === "string") query.url = route.query.url;
      return { path: route.path, query };
    },
  };
}
```

`frontend/src/report/context.ts`:
```ts
import { inject, type InjectionKey, type Ref } from "vue";

import type { ReportIndex } from "@/report/index";

/** The index of the current archive entry, provided by the report page. */
export const ReportIndexKey: InjectionKey<Ref<ReportIndex | null>> = Symbol("ReportIndex");

export function useReportIndex(): Ref<ReportIndex | null> {
  const index = inject(ReportIndexKey);
  if (!index) throw new Error("useReportIndex() outside of the report page");
  return index;
}
```

- [ ] **Step 6: Write the failing store test**

`frontend/tests/unit/reportStore.test.ts`:
```ts
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { useReportStore } from "@/stores/report";

import { loadFixture } from "./fixtures";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return { ...original, getExample: vi.fn(), getUrl: vi.fn() };
});

describe("report store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.mocked(client.getExample).mockReset();
  });

  it("loads an example and builds the indexes", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("comp_models"));
    const store = useReportStore();
    await store.loadExample("CompModels");
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    expect(store.entries).toEqual([
      "./models/omex_comp_flat.xml",
      "./models/omex_minimal.xml",
      "./models/omex_comp.xml",
    ]);
    expect(store.defaultEntry).toBe("./models/omex_comp_flat.xml");
    expect(store.indexFor("./models/omex_comp.xml")?.mainModel?.id).toBe("omex_comp");
    expect(store.source).toEqual({ kind: "example", id: "CompModels", name: "CompModels" });
  });

  it("prefers the master entry", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    expect(store.defaultEntry).toBe("./model.xml");
  });

  it("does not reload the loaded example", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    await store.loadExample("BIOMD0000000012");
    expect(client.getExample).toHaveBeenCalledTimes(1);
    await store.loadExample("BIOMD0000000001");
    expect(client.getExample).toHaveBeenCalledTimes(2);
  });

  it("stores the api error", async () => {
    vi.mocked(client.getExample).mockRejectedValue(new client.ApiError("example for id does not exist 'x'"));
    const store = useReportStore();
    await store.loadExample("x");
    expect(store.response).toBeNull();
    expect(store.error?.message).toBe("example for id does not exist 'x'");
    expect(store.loading).toBe(false);
  });
});
```

- [ ] **Step 7: Run the test to verify it fails**

Run: `npx vitest run tests/unit/reportStore.test.ts`
Expected: FAIL, cannot resolve `@/stores/report`.

- [ ] **Step 8: Write the stores**

`frontend/src/stores/report.ts` (the response and the indexes are `shallowRef`s: a 75 MB report must not become deeply reactive):
```ts
import { defineStore } from "pinia";
import { computed, markRaw, ref, shallowRef } from "vue";

import { ApiError, getExample, getUrl, postContent, postFile, toApiError } from "@/api/client";
import type { ReportResponse } from "@/api/types";
import { ReportIndex } from "@/report/index";

export type SourceKind = "example" | "url" | "file" | "content";

/** Where the current report came from. */
export interface ReportSource {
  kind: SourceKind;
  id?: string;
  url?: string;
  /** Shown while loading and in the context bar. */
  name: string;
}

function sameSource(a: ReportSource, b: ReportSource): boolean {
  return a.kind === b.kind && (a.kind === "example" ? a.id === b.id : a.kind === "url" ? a.url === b.url : false);
}

export const useReportStore = defineStore("report", () => {
  const response = shallowRef<ReportResponse | null>(null);
  const source = ref<ReportSource | null>(null);
  const loading = ref(false);
  const error = ref<ApiError | null>(null);
  const indexes = shallowRef<Map<string, ReportIndex>>(new Map());

  /** The manifest locations of the SBML entries with a report. */
  const entries = computed(() => (response.value ? Object.keys(response.value.reports) : []));

  /** The master entry if it has a report, else the first entry. */
  const defaultEntry = computed<string | null>(() => {
    const master = response.value?.manifest.entries.find(
      (entry) => entry.master && entries.value.includes(entry.location),
    );
    return master?.location ?? entries.value[0] ?? null;
  });

  function indexFor(location: string): ReportIndex | null {
    return indexes.value.get(location) ?? null;
  }

  async function load(next: ReportSource, request: () => Promise<ReportResponse>): Promise<void> {
    if (response.value && source.value && sameSource(source.value, next)) return;
    loading.value = true;
    error.value = null;
    response.value = null;
    indexes.value = new Map();
    source.value = next;
    try {
      const result = await request();
      indexes.value = new Map(
        Object.entries(result.reports).map(([location, entry]) => [
          location,
          markRaw(new ReportIndex(entry.report)),
        ]),
      );
      response.value = result;
    } catch (caught) {
      error.value = toApiError(caught);
    } finally {
      loading.value = false;
    }
  }

  const loadExample = (id: string) => load({ kind: "example", id, name: id }, () => getExample(id));
  const loadUrl = (url: string) => load({ kind: "url", url, name: url }, () => getUrl(url));
  const loadFile = (file: File) => load({ kind: "file", name: file.name }, () => postFile(file));
  const loadContent = (text: string) => load({ kind: "content", name: "pasted SBML" }, () => postContent(text));

  function clear(): void {
    response.value = null;
    source.value = null;
    error.value = null;
    indexes.value = new Map();
  }

  return { response, source, loading, error, entries, defaultEntry, indexFor, loadExample, loadUrl, loadFile, loadContent, clear };
});
```

`frontend/src/stores/examples.ts`:
```ts
import { defineStore } from "pinia";
import { ref } from "vue";

import { type ApiError, getExamples, toApiError } from "@/api/client";
import type { ExampleMetaData } from "@/api/types";

export const useExamplesStore = defineStore("examples", () => {
  const examples = ref<ExampleMetaData[]>([]);
  const loading = ref(false);
  const error = ref<ApiError | null>(null);

  /** Load the examples once. */
  async function loadExamples(): Promise<void> {
    if (examples.value.length > 0 || loading.value) return;
    loading.value = true;
    error.value = null;
    try {
      examples.value = await getExamples();
    } catch (caught) {
      error.value = toApiError(caught);
    } finally {
      loading.value = false;
    }
  }

  return { examples, loading, error, loadExamples };
});
```

- [ ] **Step 9: Run the store test**

Run: `npx vitest run tests/unit/reportStore.test.ts`
Expected: PASS (4 tests).

- [ ] **Step 10: Write the router, the layout states and the page skeletons**

`frontend/src/router.ts`:
```ts
import { createRouter, createWebHistory } from "vue-router";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: () => import("@/pages/HomePage.vue") },
    { path: "/examples", name: "examples", component: () => import("@/pages/ExamplesPage.vue") },
    { path: "/examples/:id", name: "example", component: () => import("@/pages/ReportPage.vue") },
    { path: "/report", name: "report", component: () => import("@/pages/ReportPage.vue") },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});
```

`frontend/src/components/layout/AppBar.vue`:
```vue
<script setup lang="ts"></script>

<template>
  <header
    class="flex h-12 shrink-0 items-center gap-4 border-b border-gray-200 bg-white px-4"
    data-testid="app-bar"
  >
    <RouterLink to="/" class="text-base font-semibold tracking-tight text-gray-900 hover:text-link">
      SBML4Humans
    </RouterLink>
    <div class="flex min-w-0 flex-1 items-center gap-3">
      <slot name="context" />
    </div>
    <div class="flex items-center gap-3">
      <slot name="actions" />
      <RouterLink :to="{ name: 'examples' }" class="text-sm text-gray-600 hover:text-link">Examples</RouterLink>
    </div>
  </header>
</template>
```

`frontend/src/components/layout/LoadingState.vue`:
```vue
<script setup lang="ts">
defineProps<{ message: string }>();
</script>

<template>
  <div class="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-gray-600" data-testid="loading-state">
    <i class="pi pi-spin pi-spinner text-2xl" />
    <p class="text-sm">{{ message }}</p>
  </div>
</template>
```

`frontend/src/components/layout/ErrorState.vue`:
```vue
<script setup lang="ts">
import { ref } from "vue";

import type { ApiError } from "@/api/client";

defineProps<{ error: ApiError }>();
const showTraceback = ref(false);
</script>

<template>
  <div class="m-4 rounded border border-red-200 bg-red-50 p-4 text-sm" data-testid="error-state">
    <p class="font-medium text-red-800" data-testid="error-message">{{ error.message }}</p>
    <ul v-if="error.warnings.length" class="mt-2 list-disc pl-5 text-red-700">
      <li v-for="warning in error.warnings" :key="warning">{{ warning }}</li>
    </ul>
    <button
      v-if="error.traceback"
      type="button"
      class="mt-2 text-xs text-red-700 underline"
      data-testid="error-traceback-toggle"
      @click="showTraceback = !showTraceback"
    >
      {{ showTraceback ? "Hide details" : "Show details" }}
    </button>
    <pre
      v-if="showTraceback"
      class="mt-2 max-h-96 overflow-auto rounded bg-white p-2 font-mono text-xs text-gray-800"
      data-testid="error-traceback"
      >{{ error.traceback }}</pre
    >
  </div>
</template>
```

`frontend/src/pages/HomePage.vue` (the inputs come in Task 6):
```vue
<script setup lang="ts">
import AppBar from "@/components/layout/AppBar.vue";
</script>

<template>
  <AppBar />
  <main class="mx-auto w-full max-w-3xl flex-1 px-4 py-10" data-testid="home-page">
    <h1 class="text-3xl font-semibold tracking-tight">SBML4Humans</h1>
    <p class="mt-2 text-gray-600">Interactive, human readable reports of SBML models.</p>
  </main>
</template>
```

`frontend/src/pages/ExamplesPage.vue` (the grid comes in Task 6):
```vue
<script setup lang="ts">
import AppBar from "@/components/layout/AppBar.vue";
</script>

<template>
  <AppBar />
  <main class="mx-auto w-full max-w-6xl flex-1 px-4 py-6" data-testid="examples-page">
    <h1 class="text-2xl font-semibold tracking-tight">Examples</h1>
  </main>
</template>
```

`frontend/src/pages/ReportPage.vue` (loading, error and empty states; the frame comes in Task 9):
```vue
<script setup lang="ts">
import { computed, provide, watch } from "vue";
import { useRoute } from "vue-router";

import AppBar from "@/components/layout/AppBar.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import { ReportIndexKey } from "@/report/context";
import { useReportView } from "@/report/view";
import { useReportStore } from "@/stores/report";

const route = useRoute();
const store = useReportStore();
const view = useReportView();

watch(
  () => [route.name, route.params.id, route.query.url] as const,
  ([name, id, url]) => {
    if (name === "example" && typeof id === "string") void store.loadExample(id);
    else if (name === "report" && typeof url === "string" && url) void store.loadUrl(url);
  },
  { immediate: true },
);

/** The entry of the route if it exists, else the default entry. */
const entry = computed(() => {
  const requested = view.state.value.entry;
  return requested && store.entries.includes(requested) ? requested : store.defaultEntry;
});

const index = computed(() => (entry.value ? store.indexFor(entry.value) : null));
provide(ReportIndexKey, index);

/** The model of the route if it exists in the entry, else the main model. */
const model = computed(() => {
  const current = index.value;
  if (!current) return null;
  const requested = view.state.value.model;
  return (requested ? current.model(requested) : null) ?? current.mainModel;
});
</script>

<template>
  <AppBar />
  <LoadingState v-if="store.loading" :message="`Loading ${store.source?.name ?? 'report'}`" />
  <ErrorState v-else-if="store.error" :error="store.error" />
  <div
    v-else-if="!store.response"
    class="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-gray-600"
    data-testid="no-report"
  >
    <p>No report loaded.</p>
    <RouterLink to="/" class="text-link hover:underline">Load a model</RouterLink>
  </div>
  <main v-else class="flex min-h-0 flex-1 flex-col p-4" data-testid="report-page">
    <p class="text-sm text-gray-600">
      {{ store.source?.name }}: entry {{ entry }}, model {{ model?.id }},
      {{ index?.elements.size }} elements
    </p>
  </main>
</template>
```

`frontend/src/App.vue`:
```vue
<script setup lang="ts"></script>

<template>
  <div class="flex h-full flex-col">
    <RouterView />
  </div>
</template>
```

`frontend/src/main.ts`:
```ts
import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";
import { createApp } from "vue";

import App from "@/App.vue";
import { primevueOptions } from "@/assets/primevue";
import { router } from "@/router";
import "@/assets/main.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(PrimeVue, primevueOptions);
app.directive("tooltip", Tooltip);
app.mount("#app");
```

Update `tests/unit/smoke.test.ts` so the app mounts with its plugins:
```ts
import { createPinia } from "pinia";
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "@/App.vue";
import { router } from "@/router";

describe("App", () => {
  it("renders the home page", async () => {
    await router.push("/");
    await router.isReady();
    const wrapper = mount(App, { global: { plugins: [createPinia(), router] } });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(wrapper.text()).toContain("SBML4Humans");
  });
});
```

- [ ] **Step 11: Check in the browser**

```bash
npm run test:unit && npm run format && npm run lint && npm run typecheck && npm run build
npm run dev
```

With the backend running open `http://localhost:3456/examples/BIOMD0000000012`: the app bar, then the loading state, then the line `BIOMD0000000012: entry ./model.xml, model BIOMD0000000012, 79 elements`. Open `/examples/nope`: the error state with `example for id does not exist 'nope'` and a working details toggle. Open `/report`: "No report loaded" with the link. Stop the backend and reload `/examples/BIOMD0000000012`: the error state with "not reachable". Restart the backend.

- [ ] **Step 12: Commit**

```bash
git add -A frontend/src frontend/tests/unit
git commit -m "Add the report and examples stores, the router and the page states"
```

---

### Task 6: Home page inputs, examples page and analytics

**Files:**
- Create: `frontend/src/components/input/FileUpload.vue`, `frontend/src/components/input/UrlInput.vue`, `frontend/src/components/input/PasteInput.vue`
- Modify: `frontend/src/pages/HomePage.vue`, `frontend/src/pages/ExamplesPage.vue`, `frontend/src/main.ts`
- Test: `frontend/tests/unit/homePage.test.ts`

**Interfaces:**
- Consumes: `useReportStore` (`loadFile`, `loadUrl`, `loadContent`, `loading`, `error`), `useExamplesStore`, `ErrorState`, `LoadingState`.
- Produces: the inputs emit `submit` (`FileUpload`: `File`, `UrlInput`: `string`, `PasteInput`: `string`); test ids `home-tab-upload`, `home-tab-url`, `home-tab-paste`, `file-input`, `file-dropzone`, `url-input`, `url-submit`, `paste-input`, `paste-submit`, `examples-filter`, `example-card`.

- [ ] **Step 1: Write the failing home page test**

`frontend/tests/unit/homePage.test.ts`:
```ts
import { createPinia, setActivePinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import HomePage from "@/pages/HomePage.vue";
import { router } from "@/router";

import { loadFixture } from "./fixtures";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return { ...original, getUrl: vi.fn(), postContent: vi.fn(), postFile: vi.fn() };
});

async function mountHome() {
  await router.push("/");
  await router.isReady();
  return mount(HomePage, { global: { plugins: [createPinia(), router] } });
}

describe("HomePage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    vi.mocked(client.getUrl).mockReset();
    vi.mocked(client.postContent).mockReset();
  });

  it("navigates to the report route of the url after loading it", async () => {
    vi.mocked(client.getUrl).mockResolvedValue(loadFixture("repressilator"));
    const wrapper = await mountHome();
    await wrapper.get("[data-testid=home-tab-url]").trigger("click");
    await wrapper.get("[data-testid=url-input]").setValue("https://example.org/model.xml");
    await wrapper.get("[data-testid=url-submit]").trigger("click");
    await flushPromises();
    expect(client.getUrl).toHaveBeenCalledWith("https://example.org/model.xml");
    expect(router.currentRoute.value.name).toBe("report");
    expect(router.currentRoute.value.query.url).toBe("https://example.org/model.xml");
    expect(localStorage.getItem("sbml4humans.lastUrl")).toBe("https://example.org/model.xml");
  });

  it("shows the api error inline", async () => {
    vi.mocked(client.postContent).mockRejectedValue(new client.ApiError("no SBML", "Traceback"));
    const wrapper = await mountHome();
    await wrapper.get("[data-testid=home-tab-paste]").trigger("click");
    await wrapper.get("[data-testid=paste-input]").setValue("<nonsense/>");
    await wrapper.get("[data-testid=paste-submit]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-testid=error-message]").text()).toBe("no SBML");
    expect(router.currentRoute.value.name).toBe("home");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/homePage.test.ts`
Expected: FAIL, no element `[data-testid=home-tab-url]`.

- [ ] **Step 3: Write the inputs**

`frontend/src/components/input/FileUpload.vue`:
```vue
<script setup lang="ts">
import { ref } from "vue";

const emit = defineEmits<{ submit: [file: File] }>();
const dragging = ref(false);
const input = ref<HTMLInputElement | null>(null);

function pick(files: FileList | null | undefined): void {
  const file = files?.[0];
  if (file) emit("submit", file);
}

function onDrop(event: DragEvent): void {
  dragging.value = false;
  pick(event.dataTransfer?.files);
}
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center"
    :class="dragging ? 'border-link bg-blue-50' : 'border-gray-300'"
    data-testid="file-dropzone"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <i class="pi pi-upload text-2xl text-gray-400" />
    <p class="text-sm text-gray-600">Drop an SBML file or a COMBINE archive here, or</p>
    <button
      type="button"
      class="rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
      @click="input?.click()"
    >
      Choose a file
    </button>
    <input
      ref="input"
      type="file"
      class="hidden"
      accept=".xml,.sbml,.gz,.omex,.zip"
      data-testid="file-input"
      @change="pick(($event.target as HTMLInputElement).files)"
    />
  </div>
</template>
```

`frontend/src/components/input/UrlInput.vue`:
```vue
<script setup lang="ts">
import { ref } from "vue";

const STORAGE_KEY = "sbml4humans.lastUrl";

const emit = defineEmits<{ submit: [url: string] }>();
const url = ref(localStorage.getItem(STORAGE_KEY) ?? "");

function submit(): void {
  const value = url.value.trim();
  if (!value) return;
  localStorage.setItem(STORAGE_KEY, value);
  emit("submit", value);
}
</script>

<template>
  <form class="flex gap-2" @submit.prevent="submit">
    <input
      v-model="url"
      type="url"
      required
      placeholder="https://example.org/model.xml"
      class="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-link focus:outline-none"
      data-testid="url-input"
    />
    <button
      type="submit"
      class="rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
      data-testid="url-submit"
    >
      Load
    </button>
  </form>
</template>
```

`frontend/src/components/input/PasteInput.vue`:
```vue
<script setup lang="ts">
import { ref } from "vue";

const emit = defineEmits<{ submit: [text: string] }>();
const text = ref("");
</script>

<template>
  <form class="flex flex-col gap-2" @submit.prevent="text.trim() && emit('submit', text)">
    <textarea
      v-model="text"
      rows="12"
      required
      placeholder="<?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?>&#10;<sbml ...>"
      class="w-full rounded border border-gray-300 p-2 font-mono text-xs focus:border-link focus:outline-none"
      data-testid="paste-input"
    />
    <button
      type="submit"
      class="self-end rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
      data-testid="paste-submit"
    >
      Create report
    </button>
  </form>
</template>
```

- [ ] **Step 4: Write the home page**

`frontend/src/pages/HomePage.vue`:
```vue
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import FileUpload from "@/components/input/FileUpload.vue";
import PasteInput from "@/components/input/PasteInput.vue";
import UrlInput from "@/components/input/UrlInput.vue";
import AppBar from "@/components/layout/AppBar.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import { useReportStore } from "@/stores/report";

type Tab = "upload" | "url" | "paste";
const TABS: { id: Tab; label: string }[] = [
  { id: "upload", label: "Upload" },
  { id: "url", label: "URL" },
  { id: "paste", label: "Paste" },
];

const router = useRouter();
const store = useReportStore();
const tab = ref<Tab>("upload");

async function submit(load: () => Promise<void>, route: { url?: string } = {}): Promise<void> {
  store.clear();
  await load();
  if (!store.error) await router.push({ name: "report", query: route.url ? { url: route.url } : {} });
}
</script>

<template>
  <AppBar />
  <main class="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-10" data-testid="home-page">
    <h1 class="text-3xl font-semibold tracking-tight">SBML4Humans</h1>
    <p class="mt-2 text-gray-600">
      Interactive, human readable reports of
      <a href="https://sbml.org" class="text-link hover:underline">SBML</a> models.
    </p>

    <div class="mt-8 flex gap-1 border-b border-gray-200" role="tablist">
      <button
        v-for="item in TABS"
        :key="item.id"
        type="button"
        role="tab"
        :aria-selected="tab === item.id"
        class="-mb-px border-b-2 px-3 py-2 text-sm font-medium"
        :class="tab === item.id ? 'border-gray-900 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-800'"
        :data-testid="`home-tab-${item.id}`"
        @click="tab = item.id"
      >
        {{ item.label }}
      </button>
    </div>

    <div class="mt-6">
      <LoadingState v-if="store.loading" :message="`Creating the report of ${store.source?.name ?? 'the model'}`" />
      <template v-else>
        <FileUpload v-if="tab === 'upload'" @submit="(file) => submit(() => store.loadFile(file))" />
        <UrlInput v-else-if="tab === 'url'" @submit="(url) => submit(() => store.loadUrl(url), { url })" />
        <PasteInput v-else @submit="(text) => submit(() => store.loadContent(text))" />
        <ErrorState v-if="store.error" :error="store.error" />
      </template>
    </div>

    <p class="mt-8 text-sm text-gray-600">
      Or browse the
      <RouterLink :to="{ name: 'examples' }" class="text-link hover:underline" data-testid="home-examples-link">examples</RouterLink>.
    </p>

    <footer class="mt-auto border-t border-gray-200 pt-6 text-xs text-gray-500">
      <p>
        SBML4Humans is developed on
        <a href="https://github.com/matthiaskoenig/sbml4humans" class="text-link hover:underline">GitHub</a>
        (MIT). If you use it in your work, cite
        <a href="https://zenodo.org/badge/latestdoi/55952847" class="text-link hover:underline">the Zenodo DOI</a>.
        Funded by <a href="https://summerofcode.withgoogle.com/" class="text-link hover:underline">Google Summer of Code 2021</a>
        and the German Research Foundation (DFG) within the Research Unit Programme FOR 5151
        <a href="https://qualiperf.de" class="text-link hover:underline">QuaLiPerF</a>.
        <a href="https://github.com/matthiaskoenig/sbml4humans/blob/main/frontend/privacy_notice.md" class="text-link hover:underline">Privacy notice</a>.
      </p>
      <p class="mt-1">&copy; 2021-2026 Matthias König</p>
    </footer>
  </main>
</template>
```

Check the funding text against `git show HEAD~0:frontend/components/layout/About.vue` is not possible any more (deleted in Task 1); use `git show 6bcba9e:frontend/src/components/layout/About.vue | sed -n 110,150p` to copy the exact funding sentence and its links.

- [ ] **Step 5: Write the examples page**

`frontend/src/pages/ExamplesPage.vue`:
```vue
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import AppBar from "@/components/layout/AppBar.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import { useExamplesStore } from "@/stores/examples";

const store = useExamplesStore();
const filter = ref("");

onMounted(() => void store.loadExamples());

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

const examples = computed(() => {
  const query = filter.value.trim().toLowerCase();
  return store.examples
    .map((example) => ({ ...example, text: example.description ? stripHtml(example.description) : "" }))
    .filter(
      (example) =>
        !query ||
        example.id.toLowerCase().includes(query) ||
        (example.name ?? "").toLowerCase().includes(query) ||
        example.text.toLowerCase().includes(query),
    );
});
</script>

<template>
  <AppBar />
  <main class="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6" data-testid="examples-page">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-2xl font-semibold tracking-tight">Examples</h1>
      <input
        v-model="filter"
        type="search"
        placeholder="Filter examples"
        class="w-64 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-link focus:outline-none"
        data-testid="examples-filter"
      />
    </div>
    <LoadingState v-if="store.loading" message="Loading the examples" />
    <ErrorState v-else-if="store.error" :error="store.error" />
    <ul v-else class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="examples-grid">
      <li v-for="example in examples" :key="example.id">
        <RouterLink
          :to="{ name: 'example', params: { id: example.id } }"
          class="flex h-full flex-col gap-1 rounded-lg border border-gray-200 p-3 hover:border-gray-400 hover:bg-gray-50"
          data-testid="example-card"
        >
          <span class="font-mono text-sm font-medium">{{ example.id }}</span>
          <span v-if="example.name" class="text-sm text-gray-800">{{ example.name }}</span>
          <span v-if="example.text" class="line-clamp-2 text-xs text-gray-500">{{ example.text }}</span>
          <span v-if="example.packages.length" class="mt-auto flex flex-wrap gap-1 pt-1">
            <span
              v-for="pkg in example.packages.filter((p) => p)"
              :key="pkg"
              class="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700"
              >{{ pkg }}</span
            >
          </span>
        </RouterLink>
      </li>
    </ul>
  </main>
</template>
```

- [ ] **Step 6: Add the page view tracking**

In `frontend/src/main.ts`, after `app.use(router)`:
```ts
import { createGtag } from "vue-gtag";

if (import.meta.env.PROD) {
  app.use(createGtag({ tagId: "G-TZ6E25RS0Q", pageTracker: { router } }));
}
```
`createGtag`, `tagId` and `pageTracker: { router }` are the vue-gtag 3 api; confirm the names in `node_modules/vue-gtag/README.md` and adapt if the README differs.

- [ ] **Step 7: Run the checks and check in the browser**

```bash
npm run test:unit && npm run format && npm run lint && npm run typecheck && npm run build
npm run dev
```

With the backend running: `/` shows the three tabs; upload `backend/sbml4humans/resources/models/repressilator/BIOMD0000000012_urn.xml` through the picker and by drag and drop: the loading state, then the report route with the summary line of Task 5. Back, tab URL, `https://www.ebi.ac.uk/biomodels/services/download/get-files/MODEL1207270000/2/BIOMD0000000012_url.xml`: report route with `?url=`; the url is prefilled after a reload. Tab Paste with `hello`: the error inline with details toggle. `/examples`: the grid with 80 cards, the filter narrows by `repressilator`, a card opens the report route. At every width from 400px the pages have no horizontal scroll bar.

- [ ] **Step 8: Commit**

```bash
git add -A frontend/src frontend/tests/unit
git commit -m "Add the home page inputs, the examples page and the page view tracking"
```

---

### Task 7: Shared presentation components

**Files:**
- Create: `frontend/src/components/misc/TypeMark.vue`, `BooleanMark.vue`, `ValueText.vue`, `MathView.vue`, `UnitsView.vue`, `ElementLink.vue`
- Test: `frontend/tests/unit/misc.test.ts`

**Interfaces:**
- Consumes: `typeInfo` (Task 2), `useReportIndex` and `useReportView` (Task 5), KaTeX.
- Produces:
  - `TypeMark {type: SbmlType; size?: "sm" | "md"}`: coloured square with the icon, `title` = label.
  - `BooleanMark {value: boolean | null | undefined}`: check icon, dash for null.
  - `ValueText {value: string | number | null | undefined; mono?: boolean}`: the value or a dash, numbers with up to 6 significant digits and the full value in the tooltip.
  - `MathView {math: Math | null | undefined; display?: boolean}`: KaTeX html of `latex`, tooltip `formula`, click copies the formula.
  - `UnitsView {latex: string | null | undefined; units?: string | null}`: KaTeX of the units, tooltip the units id.
  - `ElementLink {pk: string | null | undefined; label?: string | null; mark?: boolean}`: RouterLink to `routeFor(pk)` with `data-testid="element-link"` and `data-pk` when the index has the pk, else plain text of the label.

- [ ] **Step 1: Write the failing test**

`frontend/tests/unit/misc.test.ts`:
```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const tooltip = { mounted() {} };

function mountWithIndex(component: unknown, props: Record<string, unknown>) {
  return mount(component as never, {
    props,
    global: {
      plugins: [router],
      provide: { [ReportIndexKey as symbol]: ref(index) },
      directives: { tooltip },
    },
  });
}

describe("misc components", () => {
  it("renders booleans as marks", () => {
    expect(mount(BooleanMark, { props: { value: true } }).find(".pi-check").exists()).toBe(true);
    expect(mount(BooleanMark, { props: { value: false } }).text()).toBe("-");
    expect(mount(BooleanMark, { props: { value: null } }).text()).toBe("-");
  });

  it("renders missing values as a dash and rounds numbers", () => {
    expect(mount(ValueText, { props: { value: null }, global: { directives: { tooltip } } }).text()).toBe("-");
    expect(mount(ValueText, { props: { value: 0.123456789 }, global: { directives: { tooltip } } }).text()).toBe("0.123457");
    expect(mount(ValueText, { props: { value: "abc" }, global: { directives: { tooltip } } }).text()).toBe("abc");
  });

  it("renders the latex of a math with KaTeX", () => {
    const wrapper = mount(MathView, {
      props: { math: { latex: "\\frac{a}{b}", formula: "a / b" } },
      global: { directives: { tooltip } },
    });
    expect(wrapper.find(".katex").exists()).toBe(true);
    expect(mount(MathView, { props: { math: null }, global: { directives: { tooltip } } }).text()).toBe("-");
  });

  it("links a pk the index knows and shows text otherwise", async () => {
    await router.push("/examples/BIOMD0000000012?q=x");
    const species = index.mainModel!.listOfSpecies[0]!;
    const link = mountWithIndex(ElementLink, { pk: species.pk });
    const anchor = link.get("[data-testid=element-link]");
    expect(anchor.text()).toBe(species.id);
    expect(anchor.attributes("href")).toContain(`pk=${encodeURIComponent(species.pk)}`);
    expect(anchor.attributes("href")).toContain("q=x");
    const text = mountWithIndex(ElementLink, { pk: null, label: "litre" });
    expect(text.find("[data-testid=element-link]").exists()).toBe(false);
    expect(text.text()).toBe("litre");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/misc.test.ts`
Expected: FAIL, cannot resolve the components.

- [ ] **Step 3: Write the components**

`frontend/src/components/misc/TypeMark.vue`:
```vue
<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { typeInfo } from "@/data/sbmlTypes";

const props = withDefaults(defineProps<{ type: SbmlType; size?: "sm" | "md" }>(), { size: "sm" });
const info = computed(() => typeInfo(props.type));
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-sm text-gray-800"
    :class="size === 'sm' ? 'size-4 text-[10px]' : 'size-6 text-sm'"
    :style="{ backgroundColor: info.color }"
    :title="info.label"
    data-testid="type-mark"
  >
    <i class="pi" :class="info.icon" />
  </span>
</template>
```

`frontend/src/components/misc/BooleanMark.vue`:
```vue
<script setup lang="ts">
defineProps<{ value: boolean | null | undefined }>();
</script>

<template>
  <i v-if="value === true" class="pi pi-check text-xs text-gray-700" aria-label="true" />
  <span v-else class="text-gray-400">-</span>
</template>
```

`frontend/src/components/misc/ValueText.vue`:
```vue
<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ value: string | number | null | undefined; mono?: boolean }>();

const text = computed(() => {
  const { value } = props;
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : String(Number(value.toPrecision(6)));
  }
  return value;
});

const full = computed(() => (typeof props.value === "number" && text.value !== String(props.value) ? String(props.value) : undefined));
</script>

<template>
  <span v-if="text === null" class="text-gray-400">-</span>
  <span v-else v-tooltip.bottom="full" :class="{ 'font-mono': mono || typeof value === 'number' }">{{ text }}</span>
</template>
```

`frontend/src/components/misc/MathView.vue`:
```vue
<script setup lang="ts">
import katex from "katex";
import { computed } from "vue";

import type { Math } from "@/api/types";

const props = defineProps<{ math: Math | null | undefined; display?: boolean }>();

const html = computed(() =>
  props.math
    ? katex.renderToString(props.math.latex, {
        throwOnError: false,
        displayMode: props.display ?? false,
        output: "html",
      })
    : "",
);

function copy(event: MouseEvent): void {
  if (!props.math) return;
  event.stopPropagation();
  void navigator.clipboard?.writeText(props.math.formula);
}
</script>

<template>
  <span v-if="!math" class="text-gray-400">-</span>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span
    v-else
    v-tooltip.bottom="`${math.formula} (click to copy)`"
    class="cursor-copy"
    :class="{ 'block overflow-x-auto': display }"
    data-testid="math"
    @click="copy"
    v-html="html"
  />
</template>
```

`frontend/src/components/misc/UnitsView.vue`:
```vue
<script setup lang="ts">
import katex from "katex";
import { computed } from "vue";

const props = defineProps<{ latex: string | null | undefined; units?: string | null }>();

const html = computed(() =>
  props.latex ? katex.renderToString(props.latex, { throwOnError: false, output: "html" }) : "",
);
</script>

<template>
  <span v-if="!latex" class="text-gray-400">{{ units || "-" }}</span>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span v-else v-tooltip.bottom="units ?? undefined" data-testid="units" v-html="html" />
</template>
```

`frontend/src/components/misc/ElementLink.vue`:
```vue
<script setup lang="ts">
import { computed } from "vue";

import TypeMark from "@/components/misc/TypeMark.vue";
import { useReportIndex } from "@/report/context";
import { useReportView } from "@/report/view";

const props = defineProps<{ pk: string | null | undefined; label?: string | null; mark?: boolean }>();
const index = useReportIndex();
const view = useReportView();

const target = computed(() => (props.pk ? index.value?.get(props.pk) : undefined));
const text = computed(() => props.label ?? target.value?.id ?? target.value?.metaId ?? props.pk ?? "-");
</script>

<template>
  <RouterLink
    v-if="target"
    :to="view.routeFor(target.pk)"
    class="inline-flex items-center gap-1 font-mono text-link hover:underline"
    :data-pk="target.pk"
    data-testid="element-link"
    @click.stop
  >
    <TypeMark v-if="mark && target.sbmlType" :type="target.sbmlType" />
    <span>{{ text }}</span>
  </RouterLink>
  <span v-else class="font-mono" :class="{ 'text-gray-400': text === '-' }">{{ text }}</span>
</template>
```

- [ ] **Step 4: Run the test and the checks**

```bash
npx vitest run tests/unit/misc.test.ts && npm run format && npm run lint && npm run typecheck
```

Expected: PASS. If `vue/no-v-html` still reports, place the disable comment directly above the element as shown.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/misc frontend/tests/unit/misc.test.ts
git commit -m "Add the type marker, value, math, units and element link components"
```

---

### Task 8: Column definitions per element type

**Files:**
- Create: `frontend/src/report/columns/types.ts`, `frontend/src/report/columns/core.ts`, `frontend/src/report/columns/packages.ts`, `frontend/src/report/columns/index.ts`
- Test: `frontend/tests/unit/columns.test.ts`

**Interfaces:**
- Consumes: `SbmlElement`, `ElementType`, `EdgeKind` (Task 2).
- Produces:
  ```ts
  type CellKind = "id" | "text" | "number" | "boolean" | "math" | "units" | "link" | "count";
  interface ColumnDef {
    field: string;              // dotted path into the row, also the sort field
    header: string;
    kind: CellKind;
    link?: EdgeKind;            // kind "link": the edge kind used to resolve the target pk
    latexField?: string;        // kind "units": the field holding the latex, default `${field}Latex`
    width?: string;             // css width, e.g. "8rem"
  }
  const COLUMNS: Readonly<Record<ElementType, readonly ColumnDef[]>>
  function columnsOf(type: ElementType): readonly ColumnDef[]
  function fieldValue(row: object, field: string): unknown   // resolves the dotted path, "listOfX.length" included
  ```

- [ ] **Step 1: Write the failing test**

`frontend/tests/unit/columns.test.ts`:
```ts
import { describe, expect, it } from "vitest";

import { ELEMENT_TYPES } from "@/data/sbmlTypes";
import { COLUMNS, columnsOf, fieldValue } from "@/report/columns";
import { ReportIndex } from "@/report/index";

import { loadReport } from "./fixtures";

const indexes = [
  new ReportIndex(loadReport("repressilator")),
  new ReportIndex(loadReport("icg_body")),
  new ReportIndex(loadReport("fbc_example")),
  new ReportIndex(loadReport("distrib_uncertainties")),
];

describe("columns", () => {
  it("defines columns for every element type, id and name first", () => {
    for (const info of ELEMENT_TYPES) {
      const columns = columnsOf(info.type);
      expect(columns.length, info.type).toBeGreaterThanOrEqual(2);
      expect(columns[0]).toMatchObject({ field: "id", kind: "id" });
      expect(columns[1]).toMatchObject({ field: "name", kind: "text" });
      expect(new Set(columns.map((c) => c.field)).size).toBe(columns.length);
    }
  });

  it("every column field exists on the elements of the fixtures", () => {
    let checked = 0;
    for (const index of indexes) {
      for (const model of index.models) {
        for (const [type, elements] of index.byType(model.id!)) {
          for (const element of elements) {
            for (const column of COLUMNS[type]) {
              const head = column.field.split(".")[0]!;
              expect(Object.keys(element), `${type}.${column.field}`).toContain(head);
              fieldValue(element, column.field);
              checked += 1;
            }
          }
        }
      }
    }
    expect(checked).toBeGreaterThan(100);
  });

  it("link columns name an edge kind and units columns a latex field", () => {
    for (const columns of Object.values(COLUMNS)) {
      for (const column of columns) {
        if (column.kind === "link") expect(column.link).toBeDefined();
        if (column.kind !== "link") expect(column.link).toBeUndefined();
      }
    }
  });

  it("resolves dotted paths", () => {
    const row = { kineticLaw: { math: { formula: "k" } }, listOfEventAssignments: [1, 2] };
    expect(fieldValue(row, "kineticLaw.math")).toEqual({ formula: "k" });
    expect(fieldValue(row, "listOfEventAssignments.length")).toBe(2);
    expect(fieldValue(row, "nope.deeper")).toBeUndefined();
    expect(fieldValue({ kineticLaw: null }, "kineticLaw.math")).toBeUndefined();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/columns.test.ts`
Expected: FAIL, cannot resolve `@/report/columns`.

- [ ] **Step 3: Write the column definitions**

`frontend/src/report/columns/types.ts` (the types and the shared columns; `core.ts` and `packages.ts` import from here, never from `index.ts`, so no module depends on a partially initialised one):
```ts
import type { EdgeKind } from "@/api/types";

export type CellKind = "id" | "text" | "number" | "boolean" | "math" | "units" | "link" | "count";

/** One column of an element table. */
export interface ColumnDef {
  /** Dotted path into the row, also the sort field. */
  field: string;
  header: string;
  kind: CellKind;
  /** Kind "link": the edge kind that resolves the referenced element. */
  link?: EdgeKind;
  /** Kind "units": the field with the latex, default `${field}Latex`. */
  latexField?: string;
  width?: string;
}

export const ID_COLUMNS: readonly ColumnDef[] = [
  { field: "id", header: "id", kind: "id", width: "12rem" },
  { field: "name", header: "name", kind: "text", width: "14rem" },
];
```

`frontend/src/report/columns/index.ts`:
```ts
import type { ElementType } from "@/api/types";
import { CORE_COLUMNS } from "@/report/columns/core";
import { PACKAGE_COLUMNS } from "@/report/columns/packages";

export type { CellKind, ColumnDef } from "@/report/columns/types";

export const COLUMNS: Readonly<Record<ElementType, readonly ColumnDef[]>> = {
  ...CORE_COLUMNS,
  ...PACKAGE_COLUMNS,
};

export function columnsOf(type: ElementType): readonly ColumnDef[] {
  return COLUMNS[type];
}

/** The value of a dotted path, undefined when a step is missing. */
export function fieldValue(row: object, field: string): unknown {
  let value: unknown = row;
  for (const step of field.split(".")) {
    if (value === null || value === undefined) return undefined;
    value = (value as Record<string, unknown>)[step];
  }
  return value;
}
```
`index.ts` needs `import type { ColumnDef } from "@/report/columns/types";` as well for the `COLUMNS` annotation.

`frontend/src/report/columns/core.ts`:
```ts
import type { ElementType } from "@/api/types";
import { ID_COLUMNS, type ColumnDef } from "@/report/columns/types";

const MATH: ColumnDef = { field: "math", header: "math", kind: "math" };
const DERIVED_UNITS: ColumnDef = { field: "derivedUnits", header: "derived units", kind: "units", latexField: "derivedUnits" };

type CoreType = Exclude<ElementType, "Submodel" | "Port" | "GeneProduct" | "Objective">;

export const CORE_COLUMNS: Readonly<Record<CoreType, readonly ColumnDef[]>> = {
  FunctionDefinition: [...ID_COLUMNS, MATH],
  UnitDefinition: [
    ...ID_COLUMNS,
    { field: "unitsLatex", header: "units", kind: "units", latexField: "unitsLatex" },
  ],
  Compartment: [
    ...ID_COLUMNS,
    { field: "spatialDimensions", header: "dimensions", kind: "number" },
    { field: "size", header: "size", kind: "number" },
    { field: "constant", header: "constant", kind: "boolean" },
    { field: "units", header: "units", kind: "link", link: "units" },
    DERIVED_UNITS,
  ],
  Species: [
    ...ID_COLUMNS,
    { field: "compartment", header: "compartment", kind: "link", link: "compartment" },
    { field: "initialAmount", header: "initial amount", kind: "number" },
    { field: "initialConcentration", header: "initial concentration", kind: "number" },
    { field: "substanceUnits", header: "substance units", kind: "link", link: "units" },
    { field: "hasOnlySubstanceUnits", header: "only substance units", kind: "boolean" },
    { field: "boundaryCondition", header: "boundary condition", kind: "boolean" },
    { field: "constant", header: "constant", kind: "boolean" },
    DERIVED_UNITS,
  ],
  Parameter: [
    ...ID_COLUMNS,
    { field: "value", header: "value", kind: "number" },
    { field: "constant", header: "constant", kind: "boolean" },
    { field: "units", header: "units", kind: "link", link: "units" },
    DERIVED_UNITS,
  ],
  InitialAssignment: [
    ...ID_COLUMNS,
    { field: "symbol", header: "symbol", kind: "link", link: "symbol" },
    MATH,
    DERIVED_UNITS,
  ],
  AssignmentRule: [
    ...ID_COLUMNS,
    { field: "variable", header: "variable", kind: "link", link: "variable" },
    MATH,
    DERIVED_UNITS,
  ],
  RateRule: [
    ...ID_COLUMNS,
    { field: "variable", header: "variable", kind: "link", link: "variable" },
    MATH,
    DERIVED_UNITS,
  ],
  AlgebraicRule: [...ID_COLUMNS, MATH, DERIVED_UNITS],
  Constraint: [...ID_COLUMNS, MATH, { field: "message", header: "message", kind: "text" }],
  Reaction: [
    ...ID_COLUMNS,
    { field: "reversible", header: "reversible", kind: "boolean" },
    { field: "fast", header: "fast", kind: "boolean" },
    { field: "compartment", header: "compartment", kind: "link", link: "compartment" },
    { field: "equation", header: "equation", kind: "text" },
    { field: "kineticLaw.math", header: "kinetic law", kind: "math" },
    { field: "kineticLaw.derivedUnits", header: "derived units", kind: "units", latexField: "kineticLaw.derivedUnits" },
  ],
  Event: [
    ...ID_COLUMNS,
    { field: "useValuesFromTriggerTime", header: "values from trigger time", kind: "boolean" },
    { field: "trigger.math", header: "trigger", kind: "math" },
    { field: "trigger.persistent", header: "persistent", kind: "boolean" },
    { field: "trigger.initialValue", header: "initial value", kind: "boolean" },
    { field: "priority", header: "priority", kind: "math" },
    { field: "delay", header: "delay", kind: "math" },
    { field: "listOfEventAssignments.length", header: "assignments", kind: "count" },
  ],
};
```

`frontend/src/report/columns/packages.ts`:
```ts
import type { ElementType } from "@/api/types";
import { ID_COLUMNS, type ColumnDef } from "@/report/columns/types";

type PackageType = Extract<ElementType, "Submodel" | "Port" | "GeneProduct" | "Objective">;

export const PACKAGE_COLUMNS: Readonly<Record<PackageType, readonly ColumnDef[]>> = {
  Submodel: [
    ...ID_COLUMNS,
    { field: "modelRef", header: "model", kind: "link", link: "modelRef" },
    { field: "timeConversionFactor", header: "time conversion factor", kind: "link", link: "conversionFactor" },
    { field: "extentConversionFactor", header: "extent conversion factor", kind: "link", link: "conversionFactor" },
    { field: "listOfDeletions.length", header: "deletions", kind: "count" },
  ],
  Port: [
    ...ID_COLUMNS,
    { field: "portRef", header: "port ref", kind: "link", link: "port" },
    { field: "idRef", header: "id ref", kind: "link", link: "port" },
    { field: "unitRef", header: "unit ref", kind: "link", link: "port" },
    { field: "metaIdRef", header: "meta id ref", kind: "text" },
  ],
  GeneProduct: [
    ...ID_COLUMNS,
    { field: "label", header: "label", kind: "text" },
    { field: "associatedSpecies", header: "associated species", kind: "link", link: "associatedSpecies" },
  ],
  Objective: [
    ...ID_COLUMNS,
    { field: "type", header: "type", kind: "text" },
    { field: "listOfFluxObjectives.length", header: "flux objectives", kind: "count" },
  ],
};
```

- [ ] **Step 4: Run the test and the checks**

```bash
npx vitest run tests/unit/columns.test.ts && npm run format && npm run lint && npm run typecheck
```

Expected: PASS. The "every column field exists" test guards the column definitions against schema changes: when the backend renames a field, this test fails after `npm run fixtures`.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/report/columns frontend/tests/unit/columns.test.ts
git commit -m "Define the table columns of every element type"
```

---

### Task 9: Report page frame with rail, search and tables

**Files:**
- Create: `frontend/src/components/layout/SplitPane.vue`, `frontend/src/components/report/ContextBar.vue`, `frontend/src/components/report/SearchBox.vue`, `frontend/src/components/report/TypeRail.vue`, `frontend/src/components/report/ElementSection.vue`, `frontend/src/components/report/ElementTable.vue`, `frontend/src/components/report/ElementCell.vue`
- Modify: `frontend/src/pages/ReportPage.vue`
- Test: `frontend/tests/unit/elementTable.test.ts`

**Interfaces:**
- Consumes: `ReportIndex`, `matches`, `useReportView`, `columnsOf`, `fieldValue`, the misc components, `primevueOptions`.
- Produces:
  - `SplitPane {direction: "horizontal" | "vertical"; storageKey: string; initial: number; min?: number; collapsed?: boolean; sizedPane?: "first" | "second"}` with slots `first`, `second`; the size of the sized pane in px is stored under `sbml4humans.split.<storageKey>`.
  - `ContextBar {index: ReportIndex; entries: string[]; entry: string; model: Model}`: entry Select (`data-testid="entry-select"`) when `entries.length > 1`, model Select (`data-testid="model-select"`) when `index.models.length > 1`, level/version and packages (`data-testid="document-info"`).
  - `SearchBox` (`data-testid="search-input"`): bound to `state.q` through `setSearch`, debounced 150 ms, Escape clears.
  - `TypeRail {index: ReportIndex; model: Model; counts: Map<ElementType, {total: number; matched: number}>}`: document group (`data-testid="rail-document"`, `rail-model`, `rail-emd`), element group items `data-testid="rail-type-<Type>"` with checkbox `rail-toggle-<Type>` and count `rail-count-<Type>`.
  - `ElementSection {type: ElementType; rows: SbmlElement[]; total: number}` (`data-testid="section-<Type>"`, id `section-<Type>` for scrolling) wraps `ElementTable {type: ElementType; rows: SbmlElement[]}` (`data-testid="table-<Type>"`, rows `data-pk`).
  - `ElementCell {row: SbmlElement; column: ColumnDef}`.

- [ ] **Step 1: Write the failing table test**

`frontend/tests/unit/elementTable.test.ts`:
```ts
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import type { Species } from "@/api/types";
import { primevueOptions } from "@/assets/primevue";
import ElementTable from "@/components/report/ElementTable.vue";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const species = index.byType("BIOMD0000000012").get("Species") as Species[];

describe("ElementTable", () => {
  it("renders a row per element with the id, a compartment link and marks", async () => {
    await router.push("/examples/BIOMD0000000012");
    const wrapper = mount(ElementTable, {
      props: { type: "Species", rows: species },
      global: {
        plugins: [router, [PrimeVue, primevueOptions]],
        directives: { tooltip: Tooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    });
    const rows = wrapper.findAll("tbody tr[data-pk]");
    expect(rows).toHaveLength(species.length);
    expect(rows[0]!.attributes("data-pk")).toBe(species[0]!.pk);
    expect(rows[0]!.text()).toContain(species[0]!.id);
    const link = rows[0]!.find("[data-testid=element-link]");
    expect(link.exists()).toBe(true);
    expect(link.text()).toBe(species[0]!.compartment);
    expect(wrapper.findAll("thead th").map((th) => th.text())).toContain("compartment");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/elementTable.test.ts`
Expected: FAIL, cannot resolve `ElementTable.vue`.

- [ ] **Step 3: Write ElementCell and ElementTable**

`frontend/src/components/report/ElementCell.vue`:
```vue
<script setup lang="ts">
import { computed } from "vue";

import type { SbmlElement, Math } from "@/api/types";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { fieldValue, type ColumnDef } from "@/report/columns";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ row: SbmlElement; column: ColumnDef }>();
const index = useReportIndex();

const value = computed(() => fieldValue(props.row, props.column.field));
const text = computed(() => (typeof value.value === "string" ? value.value : null));

/** Kind "link": the pk of the referenced element, resolved through the edges of the row. */
const targetPk = computed(() =>
  props.column.link ? index.value?.resolve(props.row.pk, props.column.link, text.value) ?? null : null,
);

/** Kind "link" with units: the latex of the units sits next to the id. */
const unitsLatex = computed(() => {
  if (props.column.link !== "units") return null;
  const latex = fieldValue(props.row, props.column.field === "units" || props.column.field === "substanceUnits" ? "unitsLatex" : `${props.column.field}Latex`);
  return typeof latex === "string" ? latex : null;
});
</script>

<template>
  <template v-if="column.kind === 'id'">
    <span class="font-mono font-medium">{{ text ?? "-" }}</span>
  </template>
  <BooleanMark v-else-if="column.kind === 'boolean'" :value="value as boolean | null" />
  <ValueText v-else-if="column.kind === 'number' || column.kind === 'count'" :value="value as number | null" />
  <MathView v-else-if="column.kind === 'math'" :math="value as Math | null" />
  <UnitsView v-else-if="column.kind === 'units'" :latex="value as string | null" />
  <template v-else-if="column.kind === 'link'">
    <span v-if="unitsLatex" class="inline-flex items-center gap-2">
      <ElementLink :pk="targetPk" :label="text" />
      <UnitsView :latex="unitsLatex" :units="text" />
    </span>
    <ElementLink v-else :pk="targetPk" :label="text" />
  </template>
  <ValueText v-else :value="text" :mono="column.field === 'equation'" />
</template>
```

`frontend/src/components/report/ElementTable.vue`:
```vue
<script setup lang="ts">
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import { computed } from "vue";

import type { SbmlElement, ElementType } from "@/api/types";
import ElementCell from "@/components/report/ElementCell.vue";
import { columnsOf } from "@/report/columns";
import { useReportView } from "@/report/view";

const VIRTUAL_ROWS = 200;
const ROW_HEIGHT = 36;

const props = defineProps<{ type: ElementType; rows: SbmlElement[] }>();
const view = useReportView();

const columns = computed(() => columnsOf(props.type));
const selected = computed(() => props.rows.find((row) => row.pk === view.state.value.pk) ?? null);
const virtual = computed(() => props.rows.length > VIRTUAL_ROWS);

function onSelect(row: SbmlElement | null): void {
  void view.select(row ? row.pk : null);
}
</script>

<template>
  <DataTable
    :value="rows"
    data-key="pk"
    selection-mode="single"
    :selection="selected"
    :meta-key-selection="false"
    :scrollable="virtual"
    :scroll-height="virtual ? `${ROW_HEIGHT * 15}px` : undefined"
    :virtual-scroller-options="virtual ? { itemSize: ROW_HEIGHT } : undefined"
    :row-attrs="(row: SbmlElement) => ({ 'data-pk': row.pk })"
    :data-testid="`table-${type}`"
    @update:selection="onSelect"
  >
    <Column
      v-for="column in columns"
      :key="column.field"
      :field="column.field"
      :header="column.header"
      :sortable="column.kind !== 'math' && column.kind !== 'units'"
      :style="column.width ? { width: column.width } : undefined"
    >
      <template #body="{ data }">
        <ElementCell :row="data as SbmlElement" :column="column" />
      </template>
    </Column>
  </DataTable>
</template>
```

`row-attrs` is not a DataTable prop: if the rows have no `data-pk` after mounting, use the `rowClass` alternative: give every `<tr>` the class `row-${index}` is not enough for the tests, so instead bind `pt`: `:pt="{ bodyRow: ({ context, instance }) => ({ 'data-pk': instance.rowData?.pk ?? context.rowData?.pk }) }"` and inspect `context`/`instance` in the browser devtools to find where DataTable exposes the row data (PrimeVue 4 passes `instance.rowData` to the `bodyRow` section). Adjust until `tbody tr[data-pk]` exists, then keep that one binding.

- [ ] **Step 4: Run the table test**

Run: `npx vitest run tests/unit/elementTable.test.ts`
Expected: PASS.

- [ ] **Step 5: Write SplitPane**

`frontend/src/components/layout/SplitPane.vue`:
```vue
<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

const props = withDefaults(
  defineProps<{
    direction: "horizontal" | "vertical";
    storageKey: string;
    initial: number;
    min?: number;
    collapsed?: boolean;
    sizedPane?: "first" | "second";
  }>(),
  { min: 120, collapsed: false, sizedPane: "first" },
);

const key = computed(() => `sbml4humans.split.${props.storageKey}`);
const size = ref(Number(localStorage.getItem(key.value)) || props.initial);
const container = ref<HTMLElement | null>(null);
const horizontal = computed(() => props.direction === "horizontal");

let dragging = false;

function onPointerDown(event: PointerEvent): void {
  dragging = true;
  (event.target as HTMLElement).setPointerCapture(event.pointerId);
  document.body.style.cursor = horizontal.value ? "col-resize" : "row-resize";
  document.body.style.userSelect = "none";
}

function onPointerMove(event: PointerEvent): void {
  if (!dragging || !container.value) return;
  const rect = container.value.getBoundingClientRect();
  const fromStart = horizontal.value ? event.clientX - rect.left : event.clientY - rect.top;
  const total = horizontal.value ? rect.width : rect.height;
  const next = props.sizedPane === "first" ? fromStart : total - fromStart;
  size.value = Math.min(Math.max(next, props.min), total - props.min);
}

function onPointerUp(): void {
  if (!dragging) return;
  dragging = false;
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
  localStorage.setItem(key.value, String(Math.round(size.value)));
}

onBeforeUnmount(onPointerUp);

const sizedStyle = computed(() => ({ flex: `0 0 ${size.value}px`, [horizontal.value ? "width" : "height"]: `${size.value}px` }));
</script>

<template>
  <div ref="container" class="flex min-h-0 min-w-0 flex-1" :class="horizontal ? 'flex-row' : 'flex-col'">
    <div
      class="flex min-h-0 min-w-0 flex-col overflow-hidden"
      :class="sizedPane === 'first' ? '' : 'flex-1'"
      :style="sizedPane === 'first' ? sizedStyle : undefined"
    >
      <slot name="first" />
    </div>
    <template v-if="!collapsed">
      <div
        class="shrink-0 bg-gray-200 hover:bg-gray-400"
        :class="horizontal ? 'w-1 cursor-col-resize' : 'h-1 cursor-row-resize'"
        role="separator"
        data-testid="split-handle"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      />
      <div
        class="flex min-h-0 min-w-0 flex-col overflow-hidden"
        :class="sizedPane === 'second' ? '' : 'flex-1'"
        :style="sizedPane === 'second' ? sizedStyle : undefined"
      >
        <slot name="second" />
      </div>
    </template>
  </div>
</template>
```

- [ ] **Step 6: Write ContextBar and SearchBox**

`frontend/src/components/report/ContextBar.vue`:
```vue
<script setup lang="ts">
import Select from "primevue/select";
import { computed } from "vue";

import type { Model } from "@/api/types";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";

const props = defineProps<{ index: ReportIndex; entries: string[]; entry: string; model: Model }>();
const view = useReportView();

const entryOptions = computed(() => props.entries.map((location) => ({ label: location, value: location })));
const modelOptions = computed(() =>
  props.index.models.map((model) => ({
    label: `${model.id ?? model.pk}${model.kind === "modelDefinition" ? " (definition)" : ""}`,
    value: model.id ?? "",
  })),
);
const packages = computed(() => props.index.document.packages?.map((pkg) => pkg.prefix).filter((p) => p) ?? []);
</script>

<template>
  <div class="flex min-w-0 items-center gap-3 text-sm">
    <Select
      v-if="entries.length > 1"
      :model-value="entry"
      :options="entryOptions"
      option-label="label"
      option-value="value"
      data-testid="entry-select"
      @update:model-value="(value: string) => view.setEntry(value)"
    />
    <span v-else class="truncate font-mono text-gray-700" data-testid="entry-name">{{ entry }}</span>
    <Select
      v-if="index.models.length > 1"
      :model-value="model.id ?? ''"
      :options="modelOptions"
      option-label="label"
      option-value="value"
      data-testid="model-select"
      @update:model-value="(value: string) => view.setModel(value)"
    />
    <span v-else class="truncate font-mono text-gray-700" data-testid="model-name">{{ model.id }}</span>
    <span class="whitespace-nowrap text-gray-500" data-testid="document-info">
      L{{ index.document.level }}V{{ index.document.version }}
      <span v-for="pkg in packages" :key="pkg" class="ml-1 rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-700">{{ pkg }}</span>
    </span>
  </div>
</template>
```

`frontend/src/components/report/SearchBox.vue`:
```vue
<script setup lang="ts">
import { ref, watch } from "vue";

import { useReportView } from "@/report/view";

const view = useReportView();
const text = ref(view.state.value.q);
let timer: ReturnType<typeof setTimeout> | undefined;

watch(
  () => view.state.value.q,
  (q) => {
    if (q !== text.value) text.value = q;
  },
);

watch(text, (value) => {
  clearTimeout(timer);
  timer = setTimeout(() => void view.setSearch(value), 150);
});
</script>

<template>
  <div class="relative">
    <i class="pi pi-search pointer-events-none absolute top-1/2 left-2 -translate-y-1/2 text-xs text-gray-400" />
    <input
      v-model="text"
      type="search"
      placeholder="Search id, name, notes, math"
      class="w-72 rounded border border-gray-300 py-1 pr-2 pl-7 text-sm focus:border-link focus:outline-none"
      data-testid="search-input"
      @keydown.esc="text = ''"
    />
  </div>
</template>
```

- [ ] **Step 7: Write TypeRail and ElementSection**

`frontend/src/components/report/TypeRail.vue`:
```vue
<script setup lang="ts">
import { computed } from "vue";

import type { ElementType, Model } from "@/api/types";
import TypeMark from "@/components/misc/TypeMark.vue";
import { ELEMENT_TYPES, type ElementTypeInfo } from "@/data/sbmlTypes";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";

export interface TypeCount {
  total: number;
  matched: number;
}

const props = defineProps<{ index: ReportIndex; model: Model; counts: Map<ElementType, TypeCount> }>();
const view = useReportView();

const packages = computed(() => new Set(props.index.document.packages?.map((pkg) => pkg.prefix) ?? []));

/** Package types only when the document declares the package; empty types last. */
const types = computed<ElementTypeInfo[]>(() => {
  const declared = ELEMENT_TYPES.filter((info) => info.pkg === "core" || packages.value.has(info.pkg));
  const total = (info: ElementTypeInfo) => props.counts.get(info.type)?.total ?? 0;
  return [...declared.filter((info) => total(info) > 0), ...declared.filter((info) => total(info) === 0)];
});

const visible = computed(() => view.state.value.types);
const searching = computed(() => view.state.value.q.trim() !== "");

function isVisible(type: ElementType): boolean {
  return visible.value === null || visible.value.includes(type);
}

function toggle(type: ElementType): void {
  const all = ELEMENT_TYPES.map((info) => info.type);
  const current = visible.value ?? all;
  const next = current.includes(type) ? current.filter((t) => t !== type) : all.filter((t) => t === type || current.includes(t));
  void view.setTypes(next.length === all.length ? null : next);
}

function scrollTo(type: ElementType): void {
  document.getElementById(`section-${type}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function selectedClass(pk: string): string {
  return view.state.value.pk === pk ? "bg-selected" : "hover:bg-gray-100";
}
</script>

<template>
  <nav class="flex h-full flex-col overflow-y-auto py-2 text-sm" data-testid="type-rail">
    <p class="px-3 pb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Document</p>
    <button type="button" class="flex items-center gap-2 px-3 py-1 text-left" :class="selectedClass(index.document.pk)" data-testid="rail-document" @click="view.select(index.document.pk)">
      <TypeMark type="SBMLDocument" /><span class="truncate">SBMLDocument</span>
    </button>
    <button type="button" class="flex items-center gap-2 px-3 py-1 text-left" :class="selectedClass(model.pk)" data-testid="rail-model" @click="view.select(model.pk)">
      <TypeMark type="Model" /><span class="truncate font-mono">{{ model.id }}</span>
    </button>
    <button
      v-for="emd in index.externalModelDefinitions"
      :key="emd.pk"
      type="button"
      class="flex items-center gap-2 px-3 py-1 text-left"
      :class="selectedClass(emd.pk)"
      data-testid="rail-emd"
      @click="view.select(emd.pk)"
    >
      <TypeMark type="ExternalModelDefinition" /><span class="truncate font-mono">{{ emd.id }}</span>
    </button>

    <p class="px-3 pt-4 pb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Elements</p>
    <div
      v-for="info in types"
      :key="info.type"
      class="flex items-center gap-2 px-3 py-1"
      :class="(counts.get(info.type)?.total ?? 0) === 0 ? 'text-gray-400' : 'text-gray-800'"
      :data-testid="`rail-type-${info.type}`"
    >
      <input
        type="checkbox"
        class="size-3.5 accent-gray-700"
        :checked="isVisible(info.type)"
        :aria-label="`show ${info.plural}`"
        :data-testid="`rail-toggle-${info.type}`"
        @change="toggle(info.type)"
      />
      <TypeMark :type="info.type" />
      <button type="button" class="flex-1 truncate text-left hover:underline" @click="scrollTo(info.type)">
        {{ info.plural }}
      </button>
      <span class="font-mono text-xs tabular-nums" :data-testid="`rail-count-${info.type}`">
        <template v-if="searching">{{ counts.get(info.type)?.matched ?? 0 }} / </template>{{ counts.get(info.type)?.total ?? 0 }}
      </span>
    </div>
  </nav>
</template>
```

`frontend/src/components/report/ElementSection.vue`:
```vue
<script setup lang="ts">
import type { SbmlElement, ElementType } from "@/api/types";
import TypeMark from "@/components/misc/TypeMark.vue";
import ElementTable from "@/components/report/ElementTable.vue";
import { typeInfo } from "@/data/sbmlTypes";

defineProps<{ type: ElementType; rows: SbmlElement[]; total: number }>();
</script>

<template>
  <section :id="`section-${type}`" class="scroll-mt-2" :data-testid="`section-${type}`">
    <h2 class="flex items-center gap-2 px-1 pt-4 pb-2 text-sm font-semibold text-gray-800">
      <TypeMark :type="type" size="md" />
      {{ typeInfo(type).plural }}
      <span class="font-mono text-xs font-normal text-gray-500" data-testid="section-count">
        {{ rows.length === total ? total : `${rows.length} / ${total}` }}
      </span>
    </h2>
    <div class="overflow-hidden rounded border border-gray-200">
      <ElementTable :type="type" :rows="rows" />
    </div>
  </section>
</template>
```

- [ ] **Step 8: Assemble the report page**

Replace the `<main>` of `frontend/src/pages/ReportPage.vue` and extend the script:
```ts
import SplitPane from "@/components/layout/SplitPane.vue";
import ContextBar from "@/components/report/ContextBar.vue";
import ElementSection from "@/components/report/ElementSection.vue";
import SearchBox from "@/components/report/SearchBox.vue";
import TypeRail, { type TypeCount } from "@/components/report/TypeRail.vue";
import type { SbmlElement, ElementType } from "@/api/types";
import { ELEMENT_TYPES } from "@/data/sbmlTypes";
import { matches } from "@/report/search";

/** The elements of the current model per type, filtered by the search. */
const sections = computed(() => {
  const current = index.value;
  const currentModel = model.value;
  if (!current || !currentModel?.id) return [];
  const byType = current.byType(currentModel.id);
  const { q, types } = view.state.value;
  return ELEMENT_TYPES.map((info) => {
    const all = byType.get(info.type) ?? [];
    const rows = q.trim() ? all.filter((element) => matches(element, q)) : all;
    return { type: info.type, rows, total: all.length, visible: types === null || types.includes(info.type) };
  });
});

const counts = computed(() => new Map<ElementType, TypeCount>(sections.value.map((s) => [s.type, { total: s.total, matched: s.rows.length }])));
const visibleSections = computed(() => sections.value.filter((s) => s.visible && s.rows.length > 0));

const selectedPk = computed(() => view.state.value.pk);
watch([selectedPk, index], ([pk, current]) => {
  if (pk && current && !current.has(pk)) {
    console.warn(`The selected element ${pk} is not part of the report`);
    void view.select(null, "replace");
  }
});
```

```vue
<template>
  <AppBar>
    <template #context>
      <ContextBar v-if="index && model && entry" :index="index" :entries="store.entries" :entry="entry" :model="model" />
    </template>
    <template #actions>
      <SearchBox v-if="index" />
    </template>
  </AppBar>
  <LoadingState v-if="store.loading" :message="`Loading ${store.source?.name ?? 'report'}`" />
  <ErrorState v-else-if="store.error" :error="store.error" />
  <div v-else-if="!store.response" class="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-gray-600" data-testid="no-report">
    <p>No report loaded.</p>
    <RouterLink to="/" class="text-link hover:underline">Load a model</RouterLink>
  </div>
  <SplitPane v-else-if="index && model" direction="horizontal" storage-key="rail" :initial="240" :min="160" data-testid="report-page">
    <template #first>
      <TypeRail :index="index" :model="model" :counts="counts" />
    </template>
    <template #second>
      <SplitPane direction="vertical" storage-key="inspector" :initial="320" :min="160" sized-pane="second" :collapsed="!selectedPk">
        <template #first>
          <div class="h-full overflow-y-auto px-4 pb-8" data-testid="tables">
            <p v-if="visibleSections.length === 0" class="p-8 text-center text-sm text-gray-500" data-testid="no-matches">
              No elements match.
            </p>
            <ElementSection v-for="section in visibleSections" :key="section.type" :type="section.type" :rows="section.rows as SbmlElement[]" :total="section.total" />
          </div>
        </template>
        <template #second>
          <div class="h-full overflow-hidden border-t border-gray-200 bg-gray-50 p-3 text-sm" data-testid="inspector">
            Selected: <span class="font-mono">{{ selectedPk }}</span>
          </div>
        </template>
      </SplitPane>
    </template>
  </SplitPane>
</template>
```

- [ ] **Step 9: Check in the browser**

```bash
npm run test:unit && npm run format && npm run lint && npm run typecheck && npm run build
npm run dev
```

`/examples/BIOMD0000000012`: rail with the document group and 12 core types (no comp or fbc types), counts, 6 species / 12 reactions sections with KaTeX kinetic laws, sortable headers. Clicking a species row adds `?pk=` and opens the bottom pane; clicking the compartment link selects the compartment (the row of the compartment table is highlighted); the back button returns to the species. Typing `laci` in the search filters the tables and the rail shows `n / total`; Escape clears. Unchecking Reactions hides the section and writes `types=` to the url. `/examples/CompModels`: the entry Select with three entries switches the report. `/examples/model_definitions%20(model_definitions.xml)`: the model Select. `/examples/e_coli_core%20(e_coli_core.xml.gz)`: the reactions table is virtualised (15 rows high, scrolls inside). Drag both split handles, reload: the sizes persist. `/examples/BIOMD0000000012?pk=nope`: the console warns, the url loses `pk`.

If the PrimeVue Select overlay or the sort icons render unstyled, extend `primevueOptions` in `src/assets/primevue.ts` with the section named in the elements' `data-pc-section` attribute.

- [ ] **Step 10: Commit**

```bash
git add -A frontend/src frontend/tests/unit
git commit -m "Render the report page with the type rail, the search and the element tables"
```

---

### Task 10: Inspector with attributes and links

**Files:**
- Create: `frontend/src/components/inspector/InspectorPanel.vue`, `AttributeRow.vue`, `NestedTable.vue`, `AttributesColumn.vue`, `LinksColumn.vue`, `attributes/index.ts`, one `attributes/<Type>Attributes.vue` per SBML type (25 files, listed in Step 4)
- Modify: `frontend/src/pages/ReportPage.vue`
- Test: `frontend/tests/unit/inspector.test.ts`

**Interfaces:**
- Consumes: `useReportIndex`, `useReportView`, the misc components, `EDGE_KINDS`, `edgeKindLabel`, `typeInfo`.
- Produces:
  - `InspectorPanel {pk: string}` (`data-testid="inspector"`, header `inspector-type`, `inspector-id`, `inspector-name`, buttons `inspector-xml-toggle`, `inspector-close`).
  - `AttributeRow {label: string}` with default slot.
  - `NestedTable {rows: T[]; columns: {key: string; header: string}[]}` with scoped slots `cell-<key>` receiving `{row}`; default cell renders `ValueText` of `row[key]`.
  - `AttributesColumn {element: SBase}` (`data-testid="attributes-column"`), `LinksColumn {pk: string}` (`data-testid="links-column"`, groups `links-references`, `links-referenced-by`, entries are `ElementLink`s).
  - `ATTRIBUTE_COMPONENTS: Record<SbmlType, Component>` and every attributes component takes `{element: <Type>}`.
  - The XML slot is filled in Task 11 (`AnnotationsColumn`, `XmlView`); this task leaves placeholders with `data-testid="annotations-column"` and `xml-view`.

- [ ] **Step 1: Write the failing inspector test**

`frontend/tests/unit/inspector.test.ts`:
```ts
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import type { Reaction, Species } from "@/api/types";
import { primevueOptions } from "@/assets/primevue";
import AttributesColumn from "@/components/inspector/AttributesColumn.vue";
import InspectorPanel from "@/components/inspector/InspectorPanel.vue";
import LinksColumn from "@/components/inspector/LinksColumn.vue";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import { ELEMENT_TYPES, DOCUMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const fixtures = ["repressilator", "icg_body", "fbc_example", "distrib_uncertainties", "model_definitions"] as const;
const indexes = fixtures.map((name) => new ReportIndex(loadReport(name)));
const repressilator = indexes[0]!;

function mountWith(component: unknown, props: Record<string, unknown>, index: ReportIndex) {
  return mount(component as never, {
    props,
    global: {
      plugins: [router, [PrimeVue, primevueOptions]],
      directives: { tooltip: Tooltip },
      provide: { [ReportIndexKey as symbol]: ref(index) },
    },
  });
}

describe("inspector", () => {
  it("has an attributes component for every type", () => {
    for (const info of [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES]) {
      expect(ATTRIBUTE_COMPONENTS[info.type], info.type).toBeDefined();
    }
  });

  it("renders the attributes of every element of the fixtures without error", async () => {
    await router.push("/examples/x");
    let rendered = 0;
    for (const index of indexes) {
      for (const element of index.elements.values()) {
        const wrapper = mountWith(AttributesColumn, { element }, index);
        expect(wrapper.find("[data-testid=attributes-column]").exists()).toBe(true);
        wrapper.unmount();
        rendered += 1;
      }
    }
    expect(rendered).toBeGreaterThan(300);
  });

  it("shows the species attributes with a compartment link", async () => {
    await router.push("/examples/BIOMD0000000012");
    const species = repressilator.mainModel!.listOfSpecies[0] as Species;
    const wrapper = mountWith(AttributesColumn, { element: species }, repressilator);
    expect(wrapper.text()).toContain("compartment");
    const link = wrapper.find("[data-testid=element-link]");
    expect(link.text()).toBe(species.compartment);
  });

  it("lists the reactants of a reaction with links to the species reference and the species", async () => {
    const reaction = repressilator.mainModel!.listOfReactions.find((r) => r.listOfReactants.length > 0) as Reaction;
    const wrapper = mountWith(AttributesColumn, { element: reaction }, repressilator);
    const pks = wrapper.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain(reaction.listOfReactants[0]!.pk);
    expect(pks).toContain(repressilator.resolve(reaction.pk, "reactant", reaction.listOfReactants[0]!.species));
  });

  it("groups the links by kind in both directions", async () => {
    const species = repressilator.mainModel!.listOfSpecies[0] as Species;
    const wrapper = mountWith(LinksColumn, { pk: species.pk }, repressilator);
    const references = wrapper.get("[data-testid=links-references]");
    expect(references.text()).toContain("compartment");
    const referencedBy = wrapper.get("[data-testid=links-referenced-by]");
    expect(referencedBy.findAll("[data-testid=element-link]").length).toBeGreaterThan(0);
  });

  it("shows none for an element without edges", () => {
    const wrapper = mountWith(LinksColumn, { pk: "nope" }, repressilator);
    expect(wrapper.text()).toContain("none");
  });

  it("renders the header of the panel", async () => {
    const species = repressilator.mainModel!.listOfSpecies[0] as Species;
    const wrapper = mountWith(InspectorPanel, { pk: species.pk }, repressilator);
    expect(wrapper.get("[data-testid=inspector-type]").text()).toBe("Species");
    expect(wrapper.get("[data-testid=inspector-id]").text()).toBe(species.id);
    expect(wrapper.find("[data-testid=inspector-close]").exists()).toBe(true);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/inspector.test.ts`
Expected: FAIL, cannot resolve the components.

- [ ] **Step 3: Write the primitives**

`frontend/src/components/inspector/AttributeRow.vue`:
```vue
<script setup lang="ts">
defineProps<{ label: string }>();
</script>

<template>
  <div class="grid grid-cols-[10rem_minmax(0,1fr)] gap-x-3 border-b border-gray-100 py-1 text-sm" data-testid="attribute-row">
    <dt class="truncate text-gray-500" :title="label">{{ label }}</dt>
    <dd class="min-w-0 break-words"><slot /></dd>
  </div>
</template>
```

`frontend/src/components/inspector/NestedTable.vue`:
```vue
<script setup lang="ts" generic="T extends object">
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ rows: T[]; columns: { key: string; header: string }[] }>();

function cell(row: T, key: string): string | number | null {
  const value = (row as Record<string, unknown>)[key];
  return typeof value === "string" || typeof value === "number" ? value : null;
}
</script>

<template>
  <p v-if="rows.length === 0" class="text-gray-400">-</p>
  <table v-else class="w-full text-xs" data-testid="nested-table">
    <thead>
      <tr class="border-b border-gray-200 text-left text-gray-500">
        <th v-for="column in columns" :key="column.key" class="py-1 pr-3 font-medium">{{ column.header }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, i) in rows" :key="i" class="border-b border-gray-100 align-top">
        <td v-for="column in columns" :key="column.key" class="py-1 pr-3">
          <slot :name="`cell-${column.key}`" :row="row">
            <ValueText :value="cell(row, column.key)" />
          </slot>
        </td>
      </tr>
    </tbody>
  </table>
</template>
```

`frontend/src/components/inspector/attributes/index.ts`:
```ts
import type { Component } from "vue";

import type { SbmlType } from "@/api/types";

import AlgebraicRuleAttributes from "./AlgebraicRuleAttributes.vue";
import AssignmentRuleAttributes from "./AssignmentRuleAttributes.vue";
import CompartmentAttributes from "./CompartmentAttributes.vue";
import ConstraintAttributes from "./ConstraintAttributes.vue";
import EventAssignmentAttributes from "./EventAssignmentAttributes.vue";
import EventAttributes from "./EventAttributes.vue";
import ExternalModelDefinitionAttributes from "./ExternalModelDefinitionAttributes.vue";
import FunctionDefinitionAttributes from "./FunctionDefinitionAttributes.vue";
import GeneProductAttributes from "./GeneProductAttributes.vue";
import InitialAssignmentAttributes from "./InitialAssignmentAttributes.vue";
import KineticLawAttributes from "./KineticLawAttributes.vue";
import LocalParameterAttributes from "./LocalParameterAttributes.vue";
import ModelAttributes from "./ModelAttributes.vue";
import ModifierSpeciesReferenceAttributes from "./ModifierSpeciesReferenceAttributes.vue";
import ObjectiveAttributes from "./ObjectiveAttributes.vue";
import ParameterAttributes from "./ParameterAttributes.vue";
import PortAttributes from "./PortAttributes.vue";
import RateRuleAttributes from "./RateRuleAttributes.vue";
import ReactionAttributes from "./ReactionAttributes.vue";
import SBMLDocumentAttributes from "./SBMLDocumentAttributes.vue";
import SpeciesAttributes from "./SpeciesAttributes.vue";
import SpeciesReferenceAttributes from "./SpeciesReferenceAttributes.vue";
import SubmodelAttributes from "./SubmodelAttributes.vue";
import UncertaintyAttributes from "./UncertaintyAttributes.vue";
import UnitDefinitionAttributes from "./UnitDefinitionAttributes.vue";

/** The type specific attributes component of every SBML type, each taking `element`. */
export const ATTRIBUTE_COMPONENTS: Readonly<Record<SbmlType, Component>> = {
  SBMLDocument: SBMLDocumentAttributes,
  Model: ModelAttributes,
  ExternalModelDefinition: ExternalModelDefinitionAttributes,
  FunctionDefinition: FunctionDefinitionAttributes,
  UnitDefinition: UnitDefinitionAttributes,
  Compartment: CompartmentAttributes,
  Species: SpeciesAttributes,
  Parameter: ParameterAttributes,
  InitialAssignment: InitialAssignmentAttributes,
  AssignmentRule: AssignmentRuleAttributes,
  RateRule: RateRuleAttributes,
  AlgebraicRule: AlgebraicRuleAttributes,
  Constraint: ConstraintAttributes,
  Reaction: ReactionAttributes,
  Event: EventAttributes,
  Submodel: SubmodelAttributes,
  Port: PortAttributes,
  GeneProduct: GeneProductAttributes,
  Objective: ObjectiveAttributes,
  SpeciesReference: SpeciesReferenceAttributes,
  ModifierSpeciesReference: ModifierSpeciesReferenceAttributes,
  KineticLaw: KineticLawAttributes,
  LocalParameter: LocalParameterAttributes,
  EventAssignment: EventAssignmentAttributes,
  Uncertainty: UncertaintyAttributes,
};
```

- [ ] **Step 4: Write the attributes components**

Every file in `frontend/src/components/inspector/attributes/` follows the same shape: `defineProps<{ element: <Type> }>()`, `useReportIndex()` when a reference is resolved, `AttributeRow`s in specification order. `index.value?.resolve(...)` returns the pk for `ElementLink`, the id stays the label so an unresolved reference reads as text.

`SBMLDocumentAttributes.vue`:
```vue
<script setup lang="ts">
import type { SBMLDocument } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";

defineProps<{ element: SBMLDocument }>();
</script>

<template>
  <AttributeRow label="level">{{ element.level }}</AttributeRow>
  <AttributeRow label="version">{{ element.version }}</AttributeRow>
  <AttributeRow label="packages">
    <span v-if="!element.packages?.length" class="text-gray-400">-</span>
    <span v-for="pkg in element.packages" :key="pkg.prefix" class="mr-1 rounded bg-gray-100 px-1.5 py-0.5 text-xs">{{ pkg.prefix }} v{{ pkg.version }}</span>
  </AttributeRow>
</template>
```

`ModelAttributes.vue`:
```vue
<script setup lang="ts">
import type { Model } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: Model }>();
const index = useReportIndex();

const UNITS = [
  ["substance", "substanceUnits", "substanceUnitsLatex"],
  ["time", "timeUnits", "timeUnitsLatex"],
  ["volume", "volumeUnits", "volumeUnitsLatex"],
  ["area", "areaUnits", "areaUnitsLatex"],
  ["length", "lengthUnits", "lengthUnitsLatex"],
  ["extent", "extentUnits", "extentUnitsLatex"],
] as const;

const resolve = (id: string | null | undefined) => index.value?.resolve(props.element.pk, "units", id) ?? null;
</script>

<template>
  <AttributeRow label="kind">{{ element.kind ?? "model" }}</AttributeRow>
  <AttributeRow v-for="[label, idKey, latexKey] in UNITS" :key="idKey" :label="`${label} units`">
    <span class="inline-flex items-center gap-2">
      <ElementLink :pk="resolve(element[idKey])" :label="element[idKey]" />
      <UnitsView :latex="element[latexKey]" />
    </span>
  </AttributeRow>
  <AttributeRow label="conversion factor">
    <template v-if="element.conversionFactor">
      <ElementLink :pk="index?.resolve(element.pk, 'conversionFactor', element.conversionFactor.sid)" :label="element.conversionFactor.sid" />
      <ValueText :value="element.conversionFactor.value" /> <ValueText :value="element.conversionFactor.units" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
```

`ExternalModelDefinitionAttributes.vue`:
```vue
<script setup lang="ts">
import type { ExternalModelDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: ExternalModelDefinition }>();
</script>

<template>
  <AttributeRow label="source"><ValueText :value="element.source" mono /></AttributeRow>
  <AttributeRow label="model ref"><ValueText :value="element.modelRef" mono /></AttributeRow>
</template>
```

`FunctionDefinitionAttributes.vue`:
```vue
<script setup lang="ts">
import type { FunctionDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";

defineProps<{ element: FunctionDefinition }>();
</script>

<template>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
</template>
```

`UnitDefinitionAttributes.vue`:
```vue
<script setup lang="ts">
import type { UnitDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import UnitsView from "@/components/misc/UnitsView.vue";

defineProps<{ element: UnitDefinition }>();
</script>

<template>
  <AttributeRow label="units"><UnitsView :latex="element.unitsLatex" /></AttributeRow>
</template>
```

`CompartmentAttributes.vue`:
```vue
<script setup lang="ts">
import type { Compartment } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Compartment }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="spatial dimensions"><ValueText :value="element.spatialDimensions" /></AttributeRow>
  <AttributeRow label="size"><ValueText :value="element.size" /></AttributeRow>
  <AttributeRow label="constant"><BooleanMark :value="element.constant" /></AttributeRow>
  <AttributeRow label="units">
    <span class="inline-flex items-center gap-2">
      <ElementLink :pk="index?.resolve(element.pk, 'units', element.units)" :label="element.units" />
      <UnitsView :latex="element.unitsLatex" />
    </span>
  </AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
</template>
```

`SpeciesAttributes.vue`:
```vue
<script setup lang="ts">
import type { Species } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Species }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="compartment">
    <ElementLink :pk="index?.resolve(element.pk, 'compartment', element.compartment)" :label="element.compartment" />
  </AttributeRow>
  <AttributeRow label="initial amount"><ValueText :value="element.initialAmount" /></AttributeRow>
  <AttributeRow label="initial concentration"><ValueText :value="element.initialConcentration" /></AttributeRow>
  <AttributeRow label="substance units">
    <span class="inline-flex items-center gap-2">
      <ElementLink :pk="index?.resolve(element.pk, 'units', element.substanceUnits)" :label="element.substanceUnits" />
      <UnitsView :latex="element.unitsLatex" />
    </span>
  </AttributeRow>
  <AttributeRow label="only substance units"><BooleanMark :value="element.hasOnlySubstanceUnits" /></AttributeRow>
  <AttributeRow label="boundary condition"><BooleanMark :value="element.boundaryCondition" /></AttributeRow>
  <AttributeRow label="constant"><BooleanMark :value="element.constant" /></AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
  <AttributeRow v-if="element.conversionFactor" label="conversion factor">
    <ElementLink :pk="index?.resolve(element.pk, 'conversionFactor', element.conversionFactor.sid)" :label="element.conversionFactor.sid" />
    <ValueText :value="element.conversionFactor.value" />
  </AttributeRow>
  <template v-if="element.fbc">
    <AttributeRow label="chemical formula"><ValueText :value="element.fbc.chemicalFormula" mono /></AttributeRow>
    <AttributeRow label="charge"><ValueText :value="element.fbc.charge" /></AttributeRow>
  </template>
</template>
```

`ParameterAttributes.vue` (and `LocalParameterAttributes.vue` with `LocalParameter` and without the units link, local parameters have a units edge as well so keep the link):
```vue
<script setup lang="ts">
import type { Parameter } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Parameter }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="value"><ValueText :value="element.value" /></AttributeRow>
  <AttributeRow label="constant"><BooleanMark :value="element.constant" /></AttributeRow>
  <AttributeRow label="units">
    <span class="inline-flex items-center gap-2">
      <ElementLink :pk="index?.resolve(element.pk, 'units', element.units)" :label="element.units" />
      <UnitsView :latex="element.unitsLatex" />
    </span>
  </AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
</template>
```
`LocalParameterAttributes.vue` is the same file with `LocalParameter` instead of `Parameter` and without the constant row (a local parameter is always constant).

`InitialAssignmentAttributes.vue`:
```vue
<script setup lang="ts">
import type { InitialAssignment } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: InitialAssignment }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="symbol"><ElementLink :pk="index?.resolve(element.pk, 'symbol', element.symbol)" :label="element.symbol" /></AttributeRow>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
</template>
```

`AssignmentRuleAttributes.vue` and `RateRuleAttributes.vue` (type `AssignmentRule` / `RateRule`):
```vue
<script setup lang="ts">
import type { AssignmentRule } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: AssignmentRule }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="variable"><ElementLink :pk="index?.resolve(element.pk, 'variable', element.variable)" :label="element.variable" /></AttributeRow>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
</template>
```

`AlgebraicRuleAttributes.vue`: the same without the variable row, type `AlgebraicRule`.

`ConstraintAttributes.vue`:
```vue
<script setup lang="ts">
import type { Constraint } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: Constraint }>();
</script>

<template>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
  <AttributeRow label="message"><ValueText :value="element.message" /></AttributeRow>
</template>
```

`ReactionAttributes.vue`:
```vue
<script setup lang="ts">
import type { EdgeKind, Reaction } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: Reaction }>();
const index = useReportIndex();

const PARTICIPANT_COLUMNS = [
  { key: "id", header: "id" },
  { key: "species", header: "species" },
  { key: "stoichiometry", header: "stoichiometry" },
  { key: "constant", header: "constant" },
];
const MODIFIER_COLUMNS = PARTICIPANT_COLUMNS.slice(0, 2);

const species = (kind: EdgeKind, id: string) => index.value?.resolve(props.element.pk, kind, id) ?? null;
</script>

<template>
  <AttributeRow label="reversible"><BooleanMark :value="element.reversible" /></AttributeRow>
  <AttributeRow label="fast"><BooleanMark :value="element.fast" /></AttributeRow>
  <AttributeRow label="compartment">
    <ElementLink :pk="index?.resolve(element.pk, 'compartment', element.compartment)" :label="element.compartment" />
  </AttributeRow>
  <AttributeRow label="equation"><span class="font-mono">{{ element.equation }}</span></AttributeRow>
  <AttributeRow label="reactants">
    <NestedTable :rows="element.listOfReactants ?? []" :columns="PARTICIPANT_COLUMNS">
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" :label="row.id ?? row.species" /></template>
      <template #cell-species="{ row }"><ElementLink :pk="species('reactant', row.species)" :label="row.species" /></template>
      <template #cell-constant="{ row }"><BooleanMark :value="row.constant" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow label="products">
    <NestedTable :rows="element.listOfProducts ?? []" :columns="PARTICIPANT_COLUMNS">
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" :label="row.id ?? row.species" /></template>
      <template #cell-species="{ row }"><ElementLink :pk="species('product', row.species)" :label="row.species" /></template>
      <template #cell-constant="{ row }"><BooleanMark :value="row.constant" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow label="modifiers">
    <NestedTable :rows="element.listOfModifiers ?? []" :columns="MODIFIER_COLUMNS">
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" :label="row.id ?? row.species" /></template>
      <template #cell-species="{ row }"><ElementLink :pk="species('modifier', row.species)" :label="row.species" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow label="kinetic law">
    <template v-if="element.kineticLaw">
      <ElementLink :pk="element.kineticLaw.pk" :label="element.kineticLaw.id ?? 'kinetic law'" />
      <MathView :math="element.kineticLaw.math" display />
      <UnitsView :latex="element.kineticLaw.derivedUnits" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <template v-if="element.fbc">
    <AttributeRow label="lower flux bound">
      <ElementLink :pk="index?.resolve(element.pk, 'fluxBound', element.fbc.lowerFluxBound)" :label="element.fbc.lowerFluxBound" />
    </AttributeRow>
    <AttributeRow label="upper flux bound">
      <ElementLink :pk="index?.resolve(element.pk, 'fluxBound', element.fbc.upperFluxBound)" :label="element.fbc.upperFluxBound" />
    </AttributeRow>
    <AttributeRow label="gene product association"><ValueText :value="element.fbc.geneProductAssociation" mono /></AttributeRow>
    <AttributeRow label="gene products">
      <span v-if="!element.fbc.geneProducts?.length" class="text-gray-400">-</span>
      <ElementLink v-for="gp in element.fbc.geneProducts" :key="gp" class="mr-2" :pk="index?.resolve(element.pk, 'geneProduct', gp)" :label="gp" />
    </AttributeRow>
  </template>
</template>
```

`EventAttributes.vue`:
```vue
<script setup lang="ts">
import type { Event } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Event }>();
const index = useReportIndex();

const ASSIGNMENT_COLUMNS = [
  { key: "id", header: "id" },
  { key: "variable", header: "variable" },
  { key: "math", header: "math" },
];
</script>

<template>
  <AttributeRow label="values from trigger time"><BooleanMark :value="element.useValuesFromTriggerTime" /></AttributeRow>
  <AttributeRow label="trigger"><MathView :math="element.trigger?.math" display /></AttributeRow>
  <AttributeRow label="trigger initial value"><BooleanMark :value="element.trigger?.initialValue" /></AttributeRow>
  <AttributeRow label="trigger persistent"><BooleanMark :value="element.trigger?.persistent" /></AttributeRow>
  <AttributeRow label="priority"><MathView :math="element.priority" /></AttributeRow>
  <AttributeRow label="delay"><MathView :math="element.delay" /></AttributeRow>
  <AttributeRow label="event assignments">
    <NestedTable :rows="element.listOfEventAssignments ?? []" :columns="ASSIGNMENT_COLUMNS">
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" :label="row.id ?? row.variable" /></template>
      <template #cell-variable="{ row }"><ElementLink :pk="index?.resolve(row.pk, 'variable', row.variable)" :label="row.variable" /></template>
      <template #cell-math="{ row }"><MathView :math="row.math" /></template>
    </NestedTable>
  </AttributeRow>
</template>
```

`SubmodelAttributes.vue`:
```vue
<script setup lang="ts">
import type { Submodel } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Submodel }>();
const index = useReportIndex();

const DELETION_COLUMNS = [
  { key: "portRef", header: "port ref" },
  { key: "idRef", header: "id ref" },
  { key: "unitRef", header: "unit ref" },
  { key: "metaIdRef", header: "meta id ref" },
];
</script>

<template>
  <AttributeRow label="model ref"><ElementLink :pk="index?.resolve(element.pk, 'modelRef', element.modelRef)" :label="element.modelRef" /></AttributeRow>
  <AttributeRow label="time conversion factor">
    <ElementLink :pk="index?.resolve(element.pk, 'conversionFactor', element.timeConversionFactor)" :label="element.timeConversionFactor" />
  </AttributeRow>
  <AttributeRow label="extent conversion factor">
    <ElementLink :pk="index?.resolve(element.pk, 'conversionFactor', element.extentConversionFactor)" :label="element.extentConversionFactor" />
  </AttributeRow>
  <AttributeRow label="deletions"><NestedTable :rows="element.listOfDeletions ?? []" :columns="DELETION_COLUMNS" /></AttributeRow>
</template>
```

`PortAttributes.vue`:
```vue
<script setup lang="ts">
import type { Port } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: Port }>();
const index = useReportIndex();

/** The one port edge of the port; ports reference exactly one element. */
const target = () => index.value?.references(props.element.pk).find((edge) => edge.kind === "port")?.target ?? null;
</script>

<template>
  <AttributeRow label="port ref"><ValueText :value="element.portRef" mono /></AttributeRow>
  <AttributeRow label="id ref"><ElementLink v-if="element.idRef" :pk="target()" :label="element.idRef" /><span v-else class="text-gray-400">-</span></AttributeRow>
  <AttributeRow label="unit ref"><ElementLink v-if="element.unitRef" :pk="target()" :label="element.unitRef" /><span v-else class="text-gray-400">-</span></AttributeRow>
  <AttributeRow label="meta id ref"><ElementLink v-if="element.metaIdRef" :pk="target()" :label="element.metaIdRef" /><span v-else class="text-gray-400">-</span></AttributeRow>
</template>
```

`GeneProductAttributes.vue`:
```vue
<script setup lang="ts">
import type { GeneProduct } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: GeneProduct }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="label"><ValueText :value="element.label" mono /></AttributeRow>
  <AttributeRow label="associated species">
    <ElementLink :pk="index?.resolve(element.pk, 'associatedSpecies', element.associatedSpecies)" :label="element.associatedSpecies" />
  </AttributeRow>
</template>
```

`ObjectiveAttributes.vue`:
```vue
<script setup lang="ts">
import type { Objective } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Objective }>();
const index = useReportIndex();

const COLUMNS = [
  { key: "reaction", header: "reaction" },
  { key: "coefficient", header: "coefficient" },
];
</script>

<template>
  <AttributeRow label="type"><ValueText :value="element.type" /></AttributeRow>
  <AttributeRow label="flux objectives">
    <NestedTable :rows="element.listOfFluxObjectives ?? []" :columns="COLUMNS">
      <template #cell-reaction="{ row }"><ElementLink :pk="index?.resolve(element.pk, 'fluxObjective', row.reaction)" :label="row.reaction" /></template>
    </NestedTable>
  </AttributeRow>
</template>
```

`SpeciesReferenceAttributes.vue` (a species reference has no edges of its own; the species is resolved from the parent reaction, found through the incoming edges is not possible either, so the species is looked up through the reaction that lists the reference):
```vue
<script setup lang="ts">
import { computed } from "vue";

import type { Reaction, SpeciesReference } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: SpeciesReference }>();
const index = useReportIndex();

/** The reaction listing the reference and the role of the reference in it. */
const parent = computed(() => {
  const modelId = index.value?.modelOf(props.element.pk);
  if (!index.value || !modelId) return null;
  for (const reaction of index.value.byType(modelId).get("Reaction") as Reaction[]) {
    if (reaction.listOfReactants?.some((r) => r.pk === props.element.pk)) return { reaction, kind: "reactant" as const };
    if (reaction.listOfProducts?.some((r) => r.pk === props.element.pk)) return { reaction, kind: "product" as const };
  }
  return null;
});

const speciesPk = computed(() =>
  parent.value ? index.value?.resolve(parent.value.reaction.pk, parent.value.kind, props.element.species) ?? null : null,
);
</script>

<template>
  <AttributeRow label="reaction"><ElementLink :pk="parent?.reaction.pk" :label="parent?.reaction.id ?? '-'" /></AttributeRow>
  <AttributeRow label="role">{{ parent?.kind ?? "-" }}</AttributeRow>
  <AttributeRow label="species"><ElementLink :pk="speciesPk" :label="element.species" /></AttributeRow>
  <AttributeRow label="stoichiometry"><ValueText :value="element.stoichiometry" /></AttributeRow>
  <AttributeRow label="constant"><BooleanMark :value="element.constant" /></AttributeRow>
</template>
```

`ModifierSpeciesReferenceAttributes.vue`: the same lookup over `listOfModifiers` with kind `"modifier"`, rows reaction and species only, type `ModifierSpeciesReference`.

`KineticLawAttributes.vue`:
```vue
<script setup lang="ts">
import type { KineticLaw } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";

defineProps<{ element: KineticLaw }>();

const COLUMNS = [
  { key: "id", header: "id" },
  { key: "value", header: "value" },
  { key: "unitsLatex", header: "units" },
  { key: "derivedUnits", header: "derived units" },
];
</script>

<template>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
  <AttributeRow label="local parameters">
    <NestedTable :rows="element.listOfLocalParameters ?? []" :columns="COLUMNS">
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" :label="row.id" /></template>
      <template #cell-unitsLatex="{ row }"><UnitsView :latex="row.unitsLatex" :units="row.units" /></template>
      <template #cell-derivedUnits="{ row }"><UnitsView :latex="row.derivedUnits" /></template>
    </NestedTable>
  </AttributeRow>
</template>
```

`EventAssignmentAttributes.vue`:
```vue
<script setup lang="ts">
import type { EventAssignment } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: EventAssignment }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="variable"><ElementLink :pk="index?.resolve(element.pk, 'variable', element.variable)" :label="element.variable" /></AttributeRow>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
</template>
```

`UncertaintyAttributes.vue`:
```vue
<script setup lang="ts">
import type { Uncertainty } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import MathView from "@/components/misc/MathView.vue";

defineProps<{ element: Uncertainty }>();

const COLUMNS = [
  { key: "type", header: "type" },
  { key: "var", header: "var" },
  { key: "value", header: "value" },
  { key: "units", header: "units" },
  { key: "definitionUrl", header: "definition" },
  { key: "math", header: "math" },
];
</script>

<template>
  <AttributeRow label="uncert parameters">
    <NestedTable :rows="element.uncertParameters ?? []" :columns="COLUMNS">
      <template #cell-definitionUrl="{ row }">
        <a v-if="row.definitionUrl" :href="row.definitionUrl" target="_blank" rel="noopener" class="text-link hover:underline">{{ row.definitionUrl.split("/").pop() }}</a>
        <span v-else class="text-gray-400">-</span>
      </template>
      <template #cell-math="{ row }"><MathView :math="row.math" /></template>
    </NestedTable>
  </AttributeRow>
</template>
```

- [ ] **Step 5: Write AttributesColumn and LinksColumn**

`frontend/src/components/inspector/AttributesColumn.vue`:
```vue
<script setup lang="ts">
import { computed } from "vue";

import type { SBase } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: SBase }>();
const index = useReportIndex();

const component = computed(() => (props.element.sbmlType ? ATTRIBUTE_COMPONENTS[props.element.sbmlType] : null));
const sboUrl = computed(() => (props.element.sbo ? `https://identifiers.org/${props.element.sbo}` : null));
const uncertaintyColumns = [{ key: "id", header: "id" }, { key: "count", header: "parameters" }];
const uncertainties = computed(() =>
  (props.element.uncertainties ?? []).map((u) => ({ pk: u.pk, id: u.id ?? u.metaId ?? u.pk, count: u.uncertParameters?.length ?? 0 })),
);

const replacedBySubmodel = computed(() =>
  props.element.comp?.replacedBy ? index.value?.resolve(props.element.pk, "replacedBy", props.element.comp.replacedBy.submodelRef) ?? null : null,
);
const replacedElements = computed(() =>
  (props.element.comp?.replacedElements ?? []).map((replaced) => ({
    ...replaced,
    pk: index.value?.resolve(props.element.pk, "replacedElement", replaced.submodelRef) ?? null,
    ref: replaced.sbaseRef.portRef ?? replaced.sbaseRef.idRef ?? replaced.sbaseRef.unitRef ?? replaced.sbaseRef.metaIdRef ?? "-",
  })),
);
</script>

<template>
  <dl data-testid="attributes-column">
    <AttributeRow label="metaId"><ValueText :value="element.metaId" mono /></AttributeRow>
    <AttributeRow label="sbo">
      <a v-if="sboUrl" :href="sboUrl" target="_blank" rel="noopener" class="font-mono text-link hover:underline">{{ element.sbo }}</a>
      <span v-else class="text-gray-400">-</span>
    </AttributeRow>
    <template v-if="element.comp">
      <AttributeRow v-if="element.comp.replacedBy" label="replaced by">
        <ElementLink :pk="replacedBySubmodel" :label="element.comp.replacedBy.submodelRef" />
        <span class="ml-2 font-mono text-gray-600">{{ element.comp.replacedBy.sbaseRef.portRef ?? element.comp.replacedBy.sbaseRef.idRef ?? element.comp.replacedBy.sbaseRef.metaIdRef }}</span>
      </AttributeRow>
      <AttributeRow v-if="replacedElements.length" label="replaced elements">
        <NestedTable :rows="replacedElements" :columns="[{ key: 'submodelRef', header: 'submodel' }, { key: 'ref', header: 'element' }]">
          <template #cell-submodelRef="{ row }"><ElementLink :pk="row.pk" :label="row.submodelRef" /></template>
        </NestedTable>
      </AttributeRow>
    </template>
    <component :is="component" v-if="component" :element="element" />
    <AttributeRow v-if="uncertainties.length" label="uncertainties">
      <NestedTable :rows="uncertainties" :columns="uncertaintyColumns">
        <template #cell-id="{ row }"><ElementLink :pk="row.pk" :label="row.id" /></template>
      </NestedTable>
    </AttributeRow>
  </dl>
</template>
```

`frontend/src/components/inspector/LinksColumn.vue`:
```vue
<script setup lang="ts">
import { computed } from "vue";

import type { Edge, EdgeKind } from "@/api/types";
import ElementLink from "@/components/misc/ElementLink.vue";
import { EDGE_KINDS, edgeKindLabel } from "@/data/edgeKinds";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ pk: string }>();
const index = useReportIndex();

interface Group {
  kind: EdgeKind;
  label: string;
  pks: string[];
}

function group(edges: Edge[], end: "source" | "target"): Group[] {
  return EDGE_KINDS.map((kind) => ({
    kind,
    label: edgeKindLabel(kind),
    pks: [...new Set(edges.filter((edge) => edge.kind === kind).map((edge) => edge[end]))],
  })).filter((g) => g.pks.length > 0);
}

const references = computed(() => group(index.value?.references(props.pk) ?? [], "target"));
const referencedBy = computed(() => group(index.value?.referencedBy(props.pk) ?? [], "source"));
</script>

<template>
  <div class="flex flex-col gap-4 text-sm" data-testid="links-column">
    <section data-testid="links-references">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">References</h3>
      <p v-if="references.length === 0" class="text-gray-400">none</p>
      <dl v-for="g in references" :key="g.kind" class="mb-2">
        <dt class="text-xs text-gray-500">{{ g.label }}</dt>
        <dd class="flex flex-wrap gap-1">
          <ElementLink v-for="pk in g.pks" :key="pk" :pk="pk" mark class="rounded border border-gray-200 bg-white px-1.5 py-0.5" />
        </dd>
      </dl>
    </section>
    <section data-testid="links-referenced-by">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Referenced by</h3>
      <p v-if="referencedBy.length === 0" class="text-gray-400">none</p>
      <dl v-for="g in referencedBy" :key="g.kind" class="mb-2">
        <dt class="text-xs text-gray-500">{{ g.label }}</dt>
        <dd class="flex flex-wrap gap-1">
          <ElementLink v-for="pk in g.pks" :key="pk" :pk="pk" mark class="rounded border border-gray-200 bg-white px-1.5 py-0.5" />
        </dd>
      </dl>
    </section>
  </div>
</template>
```

- [ ] **Step 6: Write InspectorPanel and mount it**

`frontend/src/components/inspector/InspectorPanel.vue`:
```vue
<script setup lang="ts">
import { computed, ref, watch } from "vue";

import AttributesColumn from "@/components/inspector/AttributesColumn.vue";
import LinksColumn from "@/components/inspector/LinksColumn.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import { typeInfo } from "@/data/sbmlTypes";
import { useReportIndex } from "@/report/context";
import { useReportView } from "@/report/view";

const props = defineProps<{ pk: string }>();
const index = useReportIndex();
const view = useReportView();

const element = computed(() => index.value?.get(props.pk) ?? null);
const label = computed(() => (element.value?.sbmlType ? typeInfo(element.value.sbmlType).label : ""));
const showXml = ref(false);
watch(() => props.pk, () => (showXml.value = false));
</script>

<template>
  <aside v-if="element" class="flex h-full flex-col border-t border-gray-200 bg-white" data-testid="inspector">
    <header class="flex h-10 shrink-0 items-center gap-2 border-b border-gray-200 px-3 text-sm">
      <TypeMark v-if="element.sbmlType" :type="element.sbmlType" size="md" />
      <span class="text-gray-500" data-testid="inspector-type">{{ element.sbmlType }}</span>
      <span class="font-mono font-semibold" data-testid="inspector-id">{{ element.id ?? element.metaId ?? element.pk }}</span>
      <span v-if="element.name" class="truncate text-gray-700" data-testid="inspector-name">{{ element.name }}</span>
      <span class="flex-1" />
      <button
        type="button"
        class="rounded px-2 py-0.5 text-xs"
        :class="showXml ? 'bg-gray-900 text-white' : 'border border-gray-300 text-gray-700 hover:bg-gray-100'"
        data-testid="inspector-xml-toggle"
        @click="showXml = !showXml"
      >
        XML
      </button>
      <button type="button" class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-900" aria-label="close" data-testid="inspector-close" @click="view.select(null)">
        <i class="pi pi-times text-xs" />
      </button>
    </header>
    <div v-if="showXml" class="min-h-0 flex-1 overflow-auto p-3" data-testid="xml-view">
      <pre class="font-mono text-xs">{{ element.xml }}</pre>
    </div>
    <div v-else class="grid min-h-0 flex-1 grid-cols-3 divide-x divide-gray-200">
      <div class="overflow-y-auto p-3"><AttributesColumn :element="element" /></div>
      <div class="overflow-y-auto p-3"><LinksColumn :pk="element.pk" /></div>
      <div class="overflow-y-auto p-3 text-sm text-gray-400" data-testid="annotations-column">Annotations follow in Task 11</div>
    </div>
  </aside>
</template>
```

In `frontend/src/pages/ReportPage.vue` replace the `#second` placeholder of the vertical `SplitPane`:
```vue
<template #second>
  <InspectorPanel v-if="selectedPk" :pk="selectedPk" />
</template>
```
and import `InspectorPanel from "@/components/inspector/InspectorPanel.vue"`.

- [ ] **Step 7: Run the tests and check in the browser**

```bash
npm run test:unit && npm run format && npm run lint && npm run typecheck && npm run build
npm run dev
```

`/examples/BIOMD0000000012`, click a species: the inspector with three columns; the compartment link selects the compartment, "Referenced by" of the compartment lists the species with type markers; a reaction shows reactants/products/modifiers tables whose ids open the species reference, whose "species" open the species; the kinetic law link opens the kinetic law with its local parameters; the XML toggle shows the SBML; the close button clears `pk` and collapses the pane. `/examples/icg_body%20(icg_body.xml)`: submodels with model ref links to the external model definition, ports with links, replaced elements. `/examples/fbc_example%20(fbc_example.xml)`: flux bounds link to parameters, gene products, objectives with flux objective links. `/examples/distrib_uncertainties%20(distrib_uncertainties.xml)`: the uncertainties table, its ids open the uncertainty with its parameters.

- [ ] **Step 8: Commit**

```bash
git add -A frontend/src frontend/tests/unit
git commit -m "Add the inspector with the attributes of every type and the link groups"
```

---

### Task 11: Annotations, notes, history and XML

**Files:**
- Create: `frontend/src/api/annotations.ts`, `frontend/src/components/inspector/AnnotationsColumn.vue`, `frontend/src/components/misc/CvTermList.vue`, `frontend/src/components/misc/NotesView.vue`, `frontend/src/components/misc/HistoryView.vue`, `frontend/src/components/misc/XmlView.vue`
- Modify: `frontend/src/components/inspector/InspectorPanel.vue`
- Test: `frontend/tests/unit/annotations.test.ts`

**Interfaces:**
- Consumes: `getAnnotationResource` (Task 3), `AnnotationInfo`, `CVTerm`, `ModelHistory`.
- Produces: `resolveAnnotation(resource: string): Promise<AnnotationInfo>` cached per resource (in flight promises shared), `CvTermList {cvterms: CVTerm[]}` (`data-testid="cvterm"`, `cvterm-resource`), `NotesView {notes: string | null | undefined}` (`data-testid="notes"`), `HistoryView {history: ModelHistory | null | undefined}` (`data-testid="history"`), `XmlView {xml: string | null | undefined}` (`data-testid="xml-view"`, `xml-copy`), `AnnotationsColumn {element: SBase}` (`data-testid="annotations-column"`).

- [ ] **Step 1: Write the failing test**

`frontend/tests/unit/annotations.test.ts`:
```ts
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { resolveAnnotation, resetAnnotationCache } from "@/api/annotations";
import CvTermList from "@/components/misc/CvTermList.vue";
import NotesView from "@/components/misc/NotesView.vue";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return { ...original, getAnnotationResource: vi.fn() };
});

const info = {
  resource: "https://identifiers.org/chebi/CHEBI:15377",
  resource_normalized: null,
  collection: "chebi",
  term: "CHEBI:15377",
  label: "water",
  description: null,
  url: "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15377",
  synonyms: [],
  xrefs: [],
  errors: [],
  warnings: [],
};

describe("annotations", () => {
  afterEach(() => {
    resetAnnotationCache();
    vi.mocked(client.getAnnotationResource).mockReset();
  });

  it("caches the resolution per resource", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const [a, b] = await Promise.all([resolveAnnotation(info.resource), resolveAnnotation(info.resource)]);
    expect(a).toBe(b);
    await resolveAnnotation(info.resource);
    expect(client.getAnnotationResource).toHaveBeenCalledTimes(1);
  });

  it("renders qualifier, resource and the resolved label", async () => {
    vi.mocked(client.getAnnotationResource).mockResolvedValue(info);
    const wrapper = mount(CvTermList, { props: { cvterms: [{ qualifier: "BQB_IS", resources: [info.resource] }] } });
    expect(wrapper.text()).toContain("BQB_IS");
    await flushPromises();
    const resource = wrapper.get("[data-testid=cvterm-resource]");
    expect(resource.text()).toContain("water");
    expect(resource.get("a").attributes("href")).toBe(info.resource);
  });

  it("keeps the resource text when the resolution fails", async () => {
    vi.mocked(client.getAnnotationResource).mockRejectedValue(new client.ApiError("boom"));
    const wrapper = mount(CvTermList, { props: { cvterms: [{ qualifier: "BQB_IS", resources: ["urn:miriam:x"] }] } });
    await flushPromises();
    expect(wrapper.get("[data-testid=cvterm-resource]").text()).toContain("urn:miriam:x");
  });

  it("sanitises the notes", () => {
    const wrapper = mount(NotesView, { props: { notes: "<p>Hello <b>world</b></p><script>alert(1)</script><img src=x onerror=alert(1)>" } });
    expect(wrapper.html()).toContain("<b>world</b>");
    expect(wrapper.html()).not.toContain("<script");
    expect(wrapper.html()).not.toContain("onerror");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/annotations.test.ts`
Expected: FAIL, cannot resolve `@/api/annotations`.

- [ ] **Step 3: Write the annotation cache and the components**

`frontend/src/api/annotations.ts`:
```ts
import { getAnnotationResource } from "@/api/client";
import type { AnnotationInfo } from "@/api/types";

const cache = new Map<string, Promise<AnnotationInfo>>();

/** Resolve an annotation resource once; concurrent and later calls share the result. */
export function resolveAnnotation(resource: string): Promise<AnnotationInfo> {
  let pending = cache.get(resource);
  if (!pending) {
    pending = getAnnotationResource(resource).catch((error: unknown) => {
      cache.delete(resource);
      throw error;
    });
    cache.set(resource, pending);
  }
  return pending;
}

/** For the tests. */
export function resetAnnotationCache(): void {
  cache.clear();
}
```

`frontend/src/components/misc/CvTermList.vue`:
```vue
<script setup lang="ts">
import { reactive, watchEffect } from "vue";

import { resolveAnnotation } from "@/api/annotations";
import type { AnnotationInfo, CVTerm } from "@/api/types";

const props = defineProps<{ cvterms: CVTerm[] }>();
const resolved = reactive(new Map<string, AnnotationInfo | null>());

watchEffect(() => {
  for (const term of props.cvterms) {
    for (const resource of term.resources) {
      if (resolved.has(resource)) continue;
      resolved.set(resource, null);
      resolveAnnotation(resource)
        .then((info) => resolved.set(resource, info))
        .catch(() => resolved.delete(resource));
    }
  }
});

function href(resource: string): string {
  return resource.startsWith("http") ? resource : `https://identifiers.org/${resource.replace(/^urn:miriam:/, "")}`;
}
</script>

<template>
  <p v-if="cvterms.length === 0" class="text-gray-400">-</p>
  <ul v-else class="flex flex-col gap-2">
    <li v-for="(term, i) in cvterms" :key="i" data-testid="cvterm">
      <p class="font-mono text-xs text-gray-500">{{ term.qualifier }}</p>
      <ul class="ml-2 flex flex-col gap-0.5">
        <li v-for="resource in term.resources" :key="resource" data-testid="cvterm-resource">
          <a :href="href(resource)" target="_blank" rel="noopener" class="break-all text-link hover:underline">
            <template v-if="resolved.get(resource)?.label">{{ resolved.get(resource)!.label }}</template>
            <template v-else>{{ resource }}</template>
          </a>
          <span v-if="resolved.get(resource)?.label" class="ml-1 font-mono text-xs text-gray-500">{{ resolved.get(resource)!.term ?? resource }}</span>
          <p v-if="resolved.get(resource)?.description" class="text-xs text-gray-600">{{ resolved.get(resource)!.description }}</p>
        </li>
      </ul>
    </li>
  </ul>
</template>
```

`frontend/src/components/misc/NotesView.vue`:
```vue
<script setup lang="ts">
import DOMPurify from "dompurify";
import { computed } from "vue";

const props = defineProps<{ notes: string | null | undefined }>();
const html = computed(() => (props.notes ? DOMPurify.sanitize(props.notes, { USE_PROFILES: { html: true } }) : ""));
</script>

<template>
  <p v-if="!html" class="text-gray-400">-</p>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-else class="prose prose-sm max-w-none text-sm [&_a]:text-link [&_a]:underline [&_p]:my-1" data-testid="notes" v-html="html" />
</template>
```

`frontend/src/components/misc/HistoryView.vue`:
```vue
<script setup lang="ts">
import type { ModelHistory } from "@/api/types";

defineProps<{ history: ModelHistory | null | undefined }>();

function name(creator: { givenName?: string | null; familyName?: string | null }): string {
  return [creator.givenName, creator.familyName].filter((part) => part).join(" ") || "unknown";
}
</script>

<template>
  <p v-if="!history" class="text-gray-400">-</p>
  <div v-else class="flex flex-col gap-1 text-sm" data-testid="history">
    <p v-for="(creator, i) in history.creators" :key="i">
      {{ name(creator) }}<span v-if="creator.organization" class="text-gray-500">, {{ creator.organization }}</span>
      <a v-if="creator.email" :href="`mailto:${creator.email}`" class="ml-1 text-link hover:underline">{{ creator.email }}</a>
    </p>
    <p v-if="history.createdDate" class="text-xs text-gray-500">created {{ history.createdDate }}</p>
    <p v-for="date in history.modifiedDates" :key="date" class="text-xs text-gray-500">modified {{ date }}</p>
  </div>
</template>
```

`frontend/src/components/misc/XmlView.vue`:
```vue
<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{ xml: string | null | undefined }>();
const copied = ref(false);

async function copy(): Promise<void> {
  if (!props.xml) return;
  await navigator.clipboard.writeText(props.xml);
  copied.value = true;
  setTimeout(() => (copied.value = false), 1500);
}
</script>

<template>
  <div class="relative h-full" data-testid="xml-view">
    <button
      type="button"
      class="absolute top-2 right-2 rounded border border-gray-300 bg-white px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-100"
      data-testid="xml-copy"
      @click="copy"
    >
      {{ copied ? "Copied" : "Copy" }}
    </button>
    <pre class="h-full overflow-auto rounded bg-gray-50 p-3 font-mono text-xs leading-relaxed">{{ xml ?? "" }}</pre>
  </div>
</template>
```

`frontend/src/components/inspector/AnnotationsColumn.vue`:
```vue
<script setup lang="ts">
import type { SBase } from "@/api/types";
import CvTermList from "@/components/misc/CvTermList.vue";
import HistoryView from "@/components/misc/HistoryView.vue";
import NotesView from "@/components/misc/NotesView.vue";

defineProps<{ element: SBase }>();
</script>

<template>
  <div class="flex flex-col gap-4 text-sm" data-testid="annotations-column">
    <section>
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Annotations</h3>
      <CvTermList :cvterms="element.cvterms ?? []" />
    </section>
    <section>
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Notes</h3>
      <NotesView :notes="element.notes" />
    </section>
    <section v-if="element.history">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">History</h3>
      <HistoryView :history="element.history" />
    </section>
  </div>
</template>
```

In `InspectorPanel.vue` replace the placeholder third column by `<div class="overflow-y-auto p-3"><AnnotationsColumn :element="element" /></div>` and the XML `<div>` by `<div class="min-h-0 flex-1 overflow-hidden p-3"><XmlView :xml="element.xml" /></div>`, importing both components.

- [ ] **Step 4: Run the tests and check in the browser**

```bash
npm run test:unit && npm run format && npm run lint && npm run typecheck && npm run build
npm run dev
```

`/examples/BIOMD0000000012`: select the model in the rail: the annotations resolve to labels (network), the notes render as html with working links, the history lists the creators. Select a species with notes; `/examples/notes%20(notes.xml)`: the notes showcase renders headings, lists and tables without broken layout. The XML toggle shows the SBML with a working Copy button. Selecting another element resets the toggle.

- [ ] **Step 5: Commit**

```bash
git add -A frontend/src frontend/tests/unit
git commit -m "Show the annotations, notes, history and XML of the selected element"
```

---

### Task 12: End to end tests with Playwright

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/tests/e2e/helpers.ts`, `frontend/tests/e2e/examples.spec.ts`, `frontend/tests/e2e/report.spec.ts`, `frontend/tests/e2e/inputs.spec.ts`
- Modify: `frontend/.gitignore` (already ignores `playwright-report/`, `test-results/`)

**Interfaces:**
- Consumes: the test ids of Tasks 5 to 11, the running backend on port 1444, the Vite dev server on port 3456 (started by Playwright).
- Produces: `npm run test:e2e`.

- [ ] **Step 1: Write the Playwright configuration**

`frontend/playwright.config.ts`:
```ts
import { defineConfig, devices } from "@playwright/test";

const PORT = 3456;

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev",
    url: `http://localhost:${PORT}`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1600, height: 1000 } } }],
});
```

- [ ] **Step 2: Write the helpers and the examples test**

`frontend/tests/e2e/helpers.ts`:
```ts
import { expect, type Page } from "@playwright/test";

export const REPOSITORY = new URL("../../../", import.meta.url).pathname;
export const REPRESSILATOR_FILE = `${REPOSITORY}backend/sbml4humans/resources/models/repressilator/BIOMD0000000012_urn.xml`;

/** Open the report of an example and wait for the tables. */
export async function openExample(page: Page, id: string): Promise<void> {
  await page.goto(`/examples/${encodeURIComponent(id)}`);
  await expect(page.getByTestId("report-page")).toBeVisible();
}

export function query(page: Page, key: string): string | null {
  return new URL(page.url()).searchParams.get(key);
}
```

`frontend/tests/e2e/examples.spec.ts`:
```ts
import { expect, test } from "@playwright/test";

import { openExample } from "./helpers";

test("the examples page lists the examples and opens one", async ({ page }) => {
  await page.goto("/examples");
  const cards = page.getByTestId("example-card");
  await expect(cards.first()).toBeVisible();
  expect(await cards.count()).toBeGreaterThan(50);
  await page.getByTestId("examples-filter").fill("repressilator");
  await expect(cards).toHaveCount(2);
  await cards.first().click();
  await expect(page).toHaveURL(/\/examples\/BIOMD0000000012/);
  await expect(page.getByTestId("report-page")).toBeVisible();
});

test("every example renders its sections", async ({ page, request }) => {
  const response = await request.get("http://localhost:1444/api/examples");
  const { examples } = (await response.json()) as { examples: { id: string }[] };
  test.setTimeout(examples.length * 15_000);
  for (const example of examples) {
    await openExample(page, example.id);
    await expect(page.getByTestId("type-rail")).toBeVisible();
    const sections = page.locator("[data-testid^=section-]");
    expect(await sections.count(), example.id).toBeGreaterThan(0);
    await expect(page.getByTestId("error-state")).toHaveCount(0);
  }
});

test("an unknown example shows the api error", async ({ page }) => {
  await page.goto("/examples/nope");
  await expect(page.getByTestId("error-message")).toHaveText("example for id does not exist 'nope'");
  await page.getByTestId("error-traceback-toggle").click();
  await expect(page.getByTestId("error-traceback")).toContainText("Traceback");
});
```

- [ ] **Step 3: Write the report test**

`frontend/tests/e2e/report.spec.ts`:
```ts
import { expect, test } from "@playwright/test";

import { openExample, query } from "./helpers";

test.describe("repressilator", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, "BIOMD0000000012");
  });

  test("selects a species, follows a referenced by link and goes back", async ({ page }) => {
    const table = page.getByTestId("table-Species");
    const row = table.locator("tbody tr[data-pk]").first();
    const pk = (await row.getAttribute("data-pk"))!;
    await row.click();
    expect(query(page, "pk")).toBe(pk);
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Species");

    await inspector.getByTestId("links-references").getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Compartment");
    const compartmentPk = query(page, "pk");

    await inspector.getByTestId("links-referenced-by").getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).not.toHaveText("Compartment");
    await page.goBack();
    expect(query(page, "pk")).toBe(compartmentPk);
    await page.goBack();
    expect(query(page, "pk")).toBe(pk);

    await inspector.getByTestId("inspector-close").click();
    expect(query(page, "pk")).toBeNull();
    await expect(page.getByTestId("inspector")).toHaveCount(0);
  });

  test("the search filters the tables", async ({ page }) => {
    const speciesRows = page.getByTestId("table-Species").locator("tbody tr[data-pk]");
    const total = await speciesRows.count();
    await page.getByTestId("search-input").fill("laci");
    await expect(page.getByTestId("rail-count-Species")).toContainText("/");
    await expect.poll(() => speciesRows.count()).toBeLessThan(total);
    expect(query(page, "q")).toBe("laci");
    await page.getByTestId("search-input").fill("zzzz-nothing");
    await expect(page.getByTestId("no-matches")).toBeVisible();
    await page.getByTestId("search-input").press("Escape");
    await expect.poll(() => speciesRows.count()).toBe(total);
  });

  test("a type can be toggled off", async ({ page }) => {
    await expect(page.getByTestId("section-Reaction")).toBeVisible();
    await page.getByTestId("rail-toggle-Reaction").click();
    await expect(page.getByTestId("section-Reaction")).toHaveCount(0);
    expect(query(page, "types")).not.toContain("Reaction");
    await page.getByTestId("rail-toggle-Reaction").click();
    await expect(page.getByTestId("section-Reaction")).toBeVisible();
    expect(query(page, "types")).toBeNull();
  });

  test("the XML toggle shows the SBML of the element", async ({ page }) => {
    await page.getByTestId("rail-model").click();
    await page.getByTestId("inspector-xml-toggle").click();
    await expect(page.getByTestId("xml-view")).toContainText("<model");
  });
});

test("the archive dropdown switches the entry", async ({ page }) => {
  await openExample(page, "CompModels");
  await expect(page.getByTestId("entry-select")).toBeVisible();
  await page.getByTestId("entry-select").click();
  await page.getByRole("option", { name: "./models/omex_minimal.xml" }).click();
  expect(query(page, "entry")).toBe("./models/omex_minimal.xml");
  await expect(page.getByTestId("model-name")).toHaveText("omex_minimal");
});

test("the model dropdown switches to a model definition", async ({ page }) => {
  await openExample(page, "model_definitions (model_definitions.xml)");
  await page.getByTestId("model-select").click();
  await page.getByRole("option", { name: /m1/ }).click();
  expect(query(page, "model")).toBe("m1");
  await expect(page.getByTestId("rail-model")).toContainText("m1");
});
```

- [ ] **Step 4: Write the inputs test**

`frontend/tests/e2e/inputs.spec.ts`:
```ts
import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

import { REPRESSILATOR_FILE } from "./helpers";

test("uploads a file", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("file-input").setInputFiles(REPRESSILATOR_FILE);
  await expect(page).toHaveURL(/\/report$/);
  await expect(page.getByTestId("report-page")).toBeVisible();
  await expect(page.getByTestId("rail-model")).toContainText("BIOMD0000000012");
  await page.reload();
  await expect(page.getByTestId("no-report")).toBeVisible();
});

test("pastes SBML content", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(readFileSync(REPRESSILATOR_FILE, "utf8"));
  await page.getByTestId("paste-submit").click();
  await expect(page.getByTestId("report-page")).toBeVisible();
});

test("loads a url and remembers it", async ({ page }) => {
  const url = "https://raw.githubusercontent.com/matthiaskoenig/sbml4humans/main/backend/sbml4humans/resources/models/repressilator/BIOMD0000000012_urn.xml";
  await page.goto("/");
  await page.getByTestId("home-tab-url").click();
  await page.getByTestId("url-input").fill(url);
  await page.getByTestId("url-submit").click();
  await expect(page).toHaveURL(/\/report\?url=/);
  await expect(page.getByTestId("report-page")).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("report-page")).toBeVisible();
  await page.goto("/");
  await page.getByTestId("home-tab-url").click();
  await expect(page.getByTestId("url-input")).toHaveValue(url);
});

test("an invalid url shows the error inline", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-tab-url").click();
  await page.getByTestId("url-input").fill("https://sbml4humans.de/does-not-exist.xml");
  await page.getByTestId("url-submit").click();
  await expect(page.getByTestId("error-message")).toBeVisible();
  await expect(page).toHaveURL(/\/$/);
});
```

- [ ] **Step 5: Run the end to end tests**

With the backend running (`cd backend && uv run uvicorn sbml4humans.api:api --port 1444`):
```bash
cd frontend && npm run test:e2e
```

Expected: all tests pass. If a `getByRole("option")` does not find the Select option, open the report in the browser, click the Select and read the rendered role and text of the options (`data-pc-section="option"`), then adjust the locator to `page.locator("[data-pc-section=option]", { hasText: ... })`. If the "every example renders its sections" test is slow (Recon3D takes about 5 s in the backend plus the transfer of 75 MB), keep it; it is the regression test of the whole report over all examples.

Fix any visual defect noticed on the way (misaligned header, overflow, missing hover state), the end to end run is also the pixel check.

- [ ] **Step 6: Commit**

```bash
npm run format && npm run lint && npm run typecheck
git add frontend/playwright.config.ts frontend/tests/e2e
git commit -m "Add the end to end tests of the report, the examples and the inputs"
```

---

### Task 13: CI, containers and documentation

**Files:**
- Modify: `.github/workflows/ci.yml`, `frontend/Dockerfile-develop`, `frontend/Dockerfile-production`, `docker-compose-develop.yml`, `docker-compose-production.yml`, `frontend/README.md`, `README.md`, `CLAUDE.md`, `.gitignore`

- [ ] **Step 1: Add the frontend jobs to the CI**

In `.github/workflows/ci.yml` add after the `schema` job:
```yaml
  frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - uses: actions/setup-node@v7
        with:
          node-version-file: frontend/.nvmrc
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install the frontend
        working-directory: frontend
        run: npm ci
      - name: Check that the generated types are current
        working-directory: frontend
        run: |
          npm run types
          git diff --exit-code -- src/types/report.ts
      - name: Lint
        working-directory: frontend
        run: npm run lint
      - name: Type check
        working-directory: frontend
        run: npm run typecheck
      - name: Unit tests
        working-directory: frontend
        run: npm run test:unit
      - name: Build
        working-directory: frontend
        run: npm run build

  e2e:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - name: Install uv and set the python version
        uses: astral-sh/setup-uv@v10.0.1
        with:
          python-version: "3.14"
          enable-cache: true
      - name: Install the backend
        working-directory: backend
        run: uv sync
      - name: Start the backend
        working-directory: backend
        run: |
          uv run uvicorn sbml4humans.api:api --port 1444 &
          for i in $(seq 1 30); do curl -fs http://localhost:1444/api/examples > /dev/null && break; sleep 1; done
      - uses: actions/setup-node@v7
        with:
          node-version-file: frontend/.nvmrc
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - name: Install the frontend
        working-directory: frontend
        run: |
          npm ci
          npx playwright install --with-deps chromium
      - name: End to end tests
        working-directory: frontend
        run: npm run test:e2e
      - uses: actions/upload-artifact@v7
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report
          retention-days: 7
```

and change the release job to `needs: [test, schema, frontend, e2e]`. `actions/setup-node@v7` and `actions/upload-artifact@v7` are the current majors on 2026-09-16.

- [ ] **Step 2: Rewrite the Dockerfiles and the compose files**

`frontend/Dockerfile-develop`:
```dockerfile
FROM node:24 AS build-stage
WORKDIR /app
COPY package*.json /app/
RUN npm ci
COPY . /app/
EXPOSE 3456
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

`frontend/Dockerfile-production`:
```dockerfile
# build stage
FROM node:24 AS build-stage
WORKDIR /app
COPY package*.json /app/
RUN npm ci
COPY . /app/
RUN npm run build

# production stage: the static files are copied into the nginx volume
FROM alpine:3.22 AS production-stage
RUN mkdir -p /vue
COPY --from=build-stage /app/dist /vue

CMD ["tail", "-f", "/dev/null"]
```

In `docker-compose-develop.yml` the frontend service keeps port `8083:3456`; remove the `vue_dist:/usr/share/nginx/html` volume of the frontend service (the dev server does not use it). In `docker-compose-production.yml` remove the `API_BASE_URL` environment variables (the api url is baked in by `.env.production`) and keep the rest. Build and run the development compose once:

```bash
sudo docker compose -f docker-compose-develop.yml build
sudo docker compose -f docker-compose-develop.yml up -d
curl -s localhost:8083 | head -5    # the Vite index.html
sudo docker compose -f docker-compose-develop.yml down
```

- [ ] **Step 3: Rewrite the frontend README**

`frontend/README.md`:
```markdown
# SBML4Humans frontend

The Vue 3 application of [SBML4Humans](https://sbml4humans.de), the interactive report of SBML models. It renders the typed report the backend api in `../backend` serves, see the [main README](../README.md) for the repository layout, the docker compose setup and the releases.

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
npm run build      # type check and production build into dist/
npm run typecheck  # vue-tsc
npm run lint       # eslint and prettier --check
npm run format     # prettier --write
npm run test:unit  # vitest
npm run test:e2e   # playwright against the running backend (npx playwright install chromium once)
npm run types      # regenerate src/types/report.ts from src/schema/report.schema.json
npm run fixtures   # record tests/fixtures/*.json from the running backend
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
- [PrimeVue](https://primevue.org/) 4 in unstyled mode (DataTable, Select, Tooltip) with [Tailwind CSS](https://tailwindcss.com/) 4 and PrimeIcons, [KaTeX](https://katex.org/) for the math and units, DOMPurify for the notes.
- ESLint, Prettier, `vue-tsc`, Vitest, Playwright.
```

- [ ] **Step 4: Update the root README and CLAUDE.md**

In `README.md`:
- repository layout row of `frontend/`: `the Vue 3 application (Vite, TypeScript, Pinia, Vue Router, PrimeVue unstyled with Tailwind CSS)`.
- the "Frontend" section: node 24 through `.nvmrc`, `npm ci`, `npm run dev`, the dev server on 3456; remove the paragraph "The api returns the typed `ReportResponse`, while the current frontend still expects..." entirely.
- mention the frontend checks: `npm run lint`, `npm run typecheck`, `npm run test:unit`, `npm run test:e2e` run as GitHub Actions on every push.

In `CLAUDE.md`:
- Project paragraph: replace "The current Vue frontend still expects the old untyped report dictionary and is replaced by the frontend redesign, a separate project; until then the frontend does not render reports." by "The Vue frontend renders the typed report: one table per element type, a search, and an inspector that follows the link graph." and "The frontend is a Vue CLI 4 project (webpack 4) with TypeScript, Vuex, Vue Router and PrimeVue." by "The frontend is a Vite 8 project (node 24) with Vue 3.5, TypeScript, Pinia, Vue Router 5 and PrimeVue 4 in unstyled mode with Tailwind CSS 4."
- Commands, frontend block: `nvm use`, `npm ci`, `npm run dev` (3456), `npm run build`, `npm run lint`, `npm run typecheck`, `npm run test:unit`, `npm run test:e2e` (backend on 1444 required), `npm run types` (after a schema change, the CI diffs it), `npm run fixtures` (after a model change, by hand).
- CI sentence: the `frontend` and `e2e` jobs, the release needs all four jobs.
- Architecture, `frontend/src` paragraph: rewrite to the layout of this plan (`api/`, `stores/`, `report/` with `ReportIndex`, `search`, `query`, `columns/`, `pages/`, `components/{layout,input,report,inspector,misc}`, `data/`, `types/report.ts` generated).
- Conventions, frontend bullet: replace the node 14 / webpack 4 / `vue-router <4.6.4` bullet by: node 24 (`frontend/.nvmrc`), `package-lock.json` committed and installed with `npm ci`, TypeScript stays at 5.9 while `typescript-eslint` requires it, PrimeVue stays at 4 (MIT, PrimeVue 5 is commercial), components resolve references through `ReportIndex` and never build a pk from an id, every element an end to end test uses carries a `data-testid`.
- Deployment: `frontend/Dockerfile-develop` and `Dockerfile-production` build on node 24.

Add to `.gitignore` under `# node`: `frontend/playwright-report/` and `frontend/test-results/`.

- [ ] **Step 5: Verify everything once more**

```bash
cd frontend && npm run lint && npm run typecheck && npm run test:unit && npm run build && npm run test:e2e
cd ../backend && uv run pytest -q && uv run ruff check . && uv run ty check
git status --short
```

Expected: every command passes, the backend is untouched (`git status` shows only the files of this task).

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/ci.yml frontend/Dockerfile-develop frontend/Dockerfile-production docker-compose-develop.yml docker-compose-production.yml frontend/README.md README.md CLAUDE.md .gitignore
git commit -m "Build, test and document the new frontend in the CI and the containers"
```

Then push the branch and watch the CI run: `git push -u origin report-data-model && gh run watch`. The `e2e` job is the first run of Playwright on the runner; if `npx playwright install --with-deps chromium` fails on the ubuntu image, pin `runs-on: ubuntu-24.04`.

---

## Deviations from the spec

- PrimeVue 4.5.5 instead of 5: PrimeVue 5 is a commercial product with a license key and yearly renewal, and its terms send open source projects to PrimeVue 4 (MIT). Recorded in the spec.
- TypeScript 5.9 instead of the current 7: `typescript-eslint` supports TypeScript below 6.1 only. Recorded in the spec.
- The search text `q` is written with a replaced route, every other view state change is pushed. Recorded in the spec.
- Only the DataTable, the Select and the Tooltip directive come from PrimeVue; checkboxes, inputs, buttons and tabs are native elements styled with Tailwind, which keeps the unstyled pass through configuration to three components. Recorded in the spec.
