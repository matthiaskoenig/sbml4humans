# Replacement of PrimeVue and PrimeIcons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove `primevue` and `primeicons` from the frontend and replace the table, the dropdowns, the tooltip and the icons by own components, `@lucide/vue` and `@floating-ui/dom`, with the same behaviour and look.

**Architecture:** Pure helpers for sorting (`src/report/sort.ts`) and windowing (`src/report/rowWindow.ts`) feed a rewritten `ElementTable.vue` built on a native `<table>`. A global `v-tooltip` directive (`src/directives/tooltip.ts`) replaces the PrimeVue directive, `SelectInput.vue` wraps a native `<select>`, and Lucide components replace the PrimeIcons classes. PrimeVue is removed last, when nothing imports it anymore.

**Tech Stack:** node 24, Vite 8, Vue 3.5 (`<script setup>`, TypeScript 6.0 strict), Vue Router 5, Pinia 4, Tailwind CSS 4, `@lucide/vue` 1.47, `@floating-ui/dom` 1.8, Vitest 5 with jsdom, `@vue/test-utils`, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-17-primevue-replacement-design.md`

## Global Constraints

- Work in the worktree `/tmp/claude-1000/-home-mkoenig-git-sbml4humans/d5bdb9bb-738c-4934-9cd0-54022bb5ade4/scratchpad/wt-primevue` on the branch `replace-primevue`. All `npm`/`npx` commands run in its `frontend/` directory.
- Use node 24: prefix every shell with `export PATH=/tmp/claude-1000/-home-mkoenig-git-sbml4humans/d5bdb9bb-738c-4934-9cd0-54022bb5ade4/scratchpad/node24/bin:$PATH`. The node on the default PATH is 22 and must not be used.
- Licenses: only MIT or ISC packages are added: `@lucide/vue@^1.47.0` (ISC) and `@floating-ui/dom@^1.8.0` (MIT). No other dependency is added.
- Every task ends green: `npm run lint` (eslint and `prettier --check`), `npm run typecheck`, `npx vitest run`. Format touched files with `npx prettier --write <files>` before linting.
- End to end tests need the backend on `http://localhost:1444` (it is running; check with `curl -fs http://localhost:1444/api/examples > /dev/null`) and a free port 3456. Run them with `CI=1 npx playwright test`, so Playwright starts its own dev server of this worktree.
- Code style of the repository: comments are full sentences in the voice of the existing code (`/** ... */` above declarations, lowercase `//` line comments), no em dash character anywhere (use `-`), every element an end to end test uses carries a `data-testid`, imports ordered as in the existing files (external packages first, then `@/` imports, then relative).
- Icons are imported from `@lucide/vue` with the `Icon` suffix (`SearchIcon`, not `Search`). Lucide sets `aria-hidden="true"` itself when an icon has no `aria-label`.
- Commit messages: one descriptive sentence in the style of the history (e.g. "Add the sort of the element tables"), no conventional commit prefix, no `Co-Authored-By` line. Never modify a CHANGELOG.

---

### Task 1: Sort of the element tables

**Files:**
- Create: `frontend/src/report/sort.ts`
- Test: `frontend/tests/unit/sort.test.ts`

**Interfaces:**
- Consumes: `fieldValue(row: object, field: string): unknown` from `@/report/columns` (exists).
- Produces:
  - `export type SortOrder = 1 | -1;`
  - `export interface SortState { field: string; order: SortOrder }`
  - `export function isEmptyValue(value: unknown): boolean`
  - `export function compareValues(a: unknown, b: unknown, order: SortOrder): number`
  - `export function sortRows<T extends object>(rows: readonly T[], sort: SortState | null): T[]`

- [ ] **Step 1: Write the failing test**

`frontend/tests/unit/sort.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { compareValues, isEmptyValue, sortRows } from "@/report/sort";

describe("sort", () => {
  it("knows the empty values", () => {
    for (const value of [null, undefined, "", [], {}]) expect(isEmptyValue(value)).toBe(true);
    for (const value of [0, false, "a", [1], { a: 1 }, new Date(0)]) {
      expect(isEmptyValue(value)).toBe(false);
    }
  });

  it("sorts strings with numeric collation in both orders", () => {
    const rows = [{ id: "x10" }, { id: "x2" }, { id: "X1" }];
    expect(sortRows(rows, { field: "id", order: 1 }).map((row) => row.id)).toEqual([
      "X1",
      "x2",
      "x10",
    ]);
    expect(sortRows(rows, { field: "id", order: -1 }).map((row) => row.id)).toEqual([
      "x10",
      "x2",
      "X1",
    ]);
  });

  it("puts the empty values last in both orders", () => {
    const rows = [{ v: null }, { v: 2 }, { v: undefined }, { v: 1 }, { v: "" }];
    expect(sortRows(rows, { field: "v", order: 1 }).map((row) => row.v)).toEqual([
      1,
      2,
      null,
      undefined,
      "",
    ]);
    expect(sortRows(rows, { field: "v", order: -1 }).map((row) => row.v)).toEqual([
      2,
      1,
      null,
      undefined,
      "",
    ]);
  });

  it("compares numbers and booleans by value", () => {
    expect(compareValues(2, 10, 1)).toBeLessThan(0);
    expect(compareValues(2, 10, -1)).toBeGreaterThan(0);
    expect(compareValues(false, true, 1)).toBeLessThan(0);
    expect(compareValues(3, 3, 1)).toBe(0);
  });

  it("keeps the order of equal values and reads nested fields", () => {
    const rows = [
      { pk: "a", comp: { size: 2 } },
      { pk: "b", comp: { size: 1 } },
      { pk: "c", comp: { size: 2 } },
    ];
    expect(sortRows(rows, { field: "comp.size", order: 1 }).map((row) => row.pk)).toEqual([
      "b",
      "a",
      "c",
    ]);
    expect(sortRows(rows, { field: "comp.size", order: -1 }).map((row) => row.pk)).toEqual([
      "a",
      "c",
      "b",
    ]);
  });

  it("returns a copy in the order of the report without a sort", () => {
    const rows = [{ id: "b" }, { id: "a" }];
    const sorted = sortRows(rows, null);
    expect(sorted).toEqual(rows);
    expect(sorted).not.toBe(rows);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/sort.test.ts`
Expected: FAIL, `Failed to resolve import "@/report/sort"`.

- [ ] **Step 3: Implement**

`frontend/src/report/sort.ts`:

```ts
import { fieldValue } from "@/report/columns";

export type SortOrder = 1 | -1;

/** The sort of an element table: one column, ascending (1) or descending (-1). */
export interface SortState {
  field: string;
  order: SortOrder;
}

const collator = new Intl.Collator(undefined, { numeric: true });

/** Empty for the sort: null, undefined, the empty string, an empty array or object. */
export function isEmptyValue(value: unknown): boolean {
  if (value === null || value === undefined || value === "") return true;
  if (Array.isArray(value)) return value.length === 0;
  return (
    typeof value === "object" && !(value instanceof Date) && Object.keys(value).length === 0
  );
}

/** Compare two values of a column for `order`, with the semantics of the PrimeVue 4
 * DataTable the tables had before: empty values last in both orders, strings with numeric
 * collation (`x2` before `x10`), every other value with `<` and `>`. */
export function compareValues(a: unknown, b: unknown, order: SortOrder): number {
  const emptyA = isEmptyValue(a);
  const emptyB = isEmptyValue(b);
  if (emptyA || emptyB) return emptyA === emptyB ? 0 : emptyA ? 1 : -1;
  if (typeof a === "string" && typeof b === "string") return order * collator.compare(a, b);
  const x = a as number;
  const y = b as number;
  return order * (x < y ? -1 : x > y ? 1 : 0);
}

/** The rows sorted by `sort` (stable), a copy in the order of the report without a sort. */
export function sortRows<T extends object>(rows: readonly T[], sort: SortState | null): T[] {
  if (!sort) return [...rows];
  const values = new Map(rows.map((row) => [row, fieldValue(row, sort.field)]));
  return [...rows].sort((a, b) => compareValues(values.get(a), values.get(b), sort.order));
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npx vitest run tests/unit/sort.test.ts`
Expected: PASS, 6 tests.

- [ ] **Step 5: Lint, type check, commit**

```bash
npx prettier --write src/report/sort.ts tests/unit/sort.test.ts
npm run lint && npm run typecheck
git add src/report/sort.ts tests/unit/sort.test.ts
git commit -m "Add the sort of the element tables"
```

---

### Task 2: Row window of the windowed tables

**Files:**
- Create: `frontend/src/report/rowWindow.ts`
- Test: `frontend/tests/unit/rowWindow.test.ts`

**Interfaces:**
- Produces:
  - `export interface RowWindow { start: number; end: number; before: number; after: number }`
  - `export function rowWindow(scrollTop: number, total: number, rowHeight: number, viewportHeight: number, overscan: number): RowWindow`

- [ ] **Step 1: Write the failing test**

`frontend/tests/unit/rowWindow.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { rowWindow } from "@/report/rowWindow";

const ROW = 36;
const VIEWPORT = ROW * 15;

describe("rowWindow", () => {
  it("renders the first rows at the top", () => {
    expect(rowWindow(0, 1000, ROW, VIEWPORT, 5)).toEqual({
      start: 0,
      end: 20,
      before: 0,
      after: 980 * ROW,
    });
  });

  it("starts the window at the partially visible row", () => {
    expect(rowWindow(50, 1000, ROW, VIEWPORT, 5)).toMatchObject({ start: 0, end: 21 });
  });

  it("renders the rows in view with the overscan in the middle", () => {
    expect(rowWindow(ROW * 500, 1000, ROW, VIEWPORT, 5)).toEqual({
      start: 495,
      end: 520,
      before: 495 * ROW,
      after: 480 * ROW,
    });
  });

  it("ends at the last row", () => {
    expect(rowWindow(ROW * 1000 - VIEWPORT, 1000, ROW, VIEWPORT, 5)).toEqual({
      start: 980,
      end: 1000,
      before: 980 * ROW,
      after: 0,
    });
  });

  it("renders every row of a list shorter than the viewport", () => {
    expect(rowWindow(0, 10, ROW, VIEWPORT, 5)).toEqual({ start: 0, end: 10, before: 0, after: 0 });
  });

  it("keeps the height of the list for every scroll position", () => {
    for (const scrollTop of [-10, 0, 1, 35, 36, 7000, 35460, 36000, 99999]) {
      const { start, end, before, after } = rowWindow(scrollTop, 1000, ROW, VIEWPORT, 5);
      expect(start).toBeLessThanOrEqual(end);
      expect(before + (end - start) * ROW + after).toBe(1000 * ROW);
    }
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npx vitest run tests/unit/rowWindow.test.ts`
Expected: FAIL, `Failed to resolve import "@/report/rowWindow"`.

- [ ] **Step 3: Implement**

`frontend/src/report/rowWindow.ts`:

```ts
/** The rows of a windowed table to render and the spacers around them. */
export interface RowWindow {
  /** Index of the first rendered row. */
  start: number;
  /** Index after the last rendered row. */
  end: number;
  /** Height of the spacer before the first rendered row. */
  before: number;
  /** Height of the spacer after the last rendered row. */
  after: number;
}

/** The window of a list of `total` rows of `rowHeight` in a viewport of `viewportHeight`
 * scrolled to `scrollTop`, with `overscan` rows more on each side. The rows have a fixed
 * height, so the window follows from the scroll position without measuring. */
export function rowWindow(
  scrollTop: number,
  total: number,
  rowHeight: number,
  viewportHeight: number,
  overscan: number,
): RowWindow {
  const first = Math.floor(Math.max(0, scrollTop) / rowHeight);
  const start = Math.min(total, Math.max(0, first - overscan));
  const end = Math.max(
    start,
    Math.min(total, first + Math.ceil(viewportHeight / rowHeight) + overscan),
  );
  return { start, end, before: start * rowHeight, after: (total - end) * rowHeight };
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npx vitest run tests/unit/rowWindow.test.ts`
Expected: PASS, 6 tests.

- [ ] **Step 5: Lint, type check, commit**

```bash
npx prettier --write src/report/rowWindow.ts tests/unit/rowWindow.test.ts
npm run lint && npm run typecheck
git add src/report/rowWindow.ts tests/unit/rowWindow.test.ts
git commit -m "Add the row window of the windowed element tables"
```

---

### Task 3: Tooltip directive

**Files:**
- Create: `frontend/src/directives/tooltip.ts`
- Test: `frontend/tests/unit/tooltip.test.ts`
- Modify: `frontend/src/main.ts` (register the own directive instead of `primevue/tooltip`)
- Modify: `frontend/tests/unit/inspector.test.ts`, `frontend/tests/unit/reportPage.test.ts`, `frontend/tests/unit/elementTable.test.ts` (use `vTooltip` instead of `primevue/tooltip`; the PrimeVue plugin stays in these tests until Task 7)
- Modify: `frontend/package.json`, `frontend/package-lock.json` (add `@floating-ui/dom`)

**Interfaces:**
- Produces:
  - `export const TOOLTIP_ID = "app-tooltip";`
  - `export const vTooltip: Directive<HTMLElement, string | null | undefined>` registered globally as `tooltip`; placement modifiers `top` (default), `bottom`, `left`, `right`.
- Call sites stay as they are: `v-tooltip.bottom="..."` in `MathView.vue`, `ValueText.vue`, `UnitsView.vue`.

- [ ] **Step 1: Add the dependency**

```bash
npm install @floating-ui/dom@^1.8.0
```

Expected: `package.json` lists `"@floating-ui/dom": "^1.8.0"` under `dependencies`; `npm audit` reports 0 vulnerabilities.

- [ ] **Step 2: Write the failing test**

`frontend/tests/unit/tooltip.test.ts`:

```ts
import * as floating from "@floating-ui/dom";
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, withDirectives } from "vue";

import { TOOLTIP_ID, vTooltip } from "@/directives/tooltip";

vi.mock("@floating-ui/dom", async (importOriginal) => {
  const original = await importOriginal<typeof floating>();
  return { ...original, computePosition: vi.fn(async () => ({ x: 12.4, y: 30.6 })) };
});

const computePosition = vi.mocked(floating.computePosition);

/** A span with the tooltip below it, as the call sites use it. */
const Host = defineComponent({
  props: { text: { type: String, required: false, default: undefined } },
  setup(props) {
    return () =>
      withDirectives(h("span", { "data-testid": "host", tabindex: 0 }, "value"), [
        [vTooltip, props.text, "", { bottom: true }],
      ]);
  },
});

let wrapper: { unmount(): void } | null = null;

function mountHost(text: string | undefined) {
  const mounted = mount(Host, { props: { text }, attachTo: document.body });
  wrapper = mounted;
  return mounted;
}

const tooltip = () => document.getElementById(TOOLTIP_ID);
const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
  computePosition.mockClear();
});

describe("v-tooltip", () => {
  it("shows the text on mouseenter and hides it on mouseleave", async () => {
    const host = mountHost("kd_mRNA * X (click to copy)").get("[data-testid=host]");
    await host.trigger("mouseenter");
    expect(tooltip()?.hidden).toBe(false);
    expect(tooltip()?.textContent).toBe("kd_mRNA * X (click to copy)");
    expect(tooltip()?.getAttribute("role")).toBe("tooltip");
    expect(host.attributes("aria-describedby")).toBe(TOOLTIP_ID);
    await host.trigger("mouseleave");
    expect(tooltip()?.hidden).toBe(true);
    expect(host.attributes("aria-describedby")).toBeUndefined();
  });

  it("positions the tooltip with the placement of the modifier", async () => {
    await mountHost("0.123456789").get("[data-testid=host]").trigger("mouseenter");
    await flush();
    expect(computePosition).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      tooltip(),
      expect.objectContaining({ placement: "bottom", strategy: "fixed" }),
    );
    expect(tooltip()?.style.transform).toBe("translate(12px, 31px)");
  });

  it("shows on keyboard focus and hides on Escape", async () => {
    await mountHost("value").get("[data-testid=host]").trigger("focusin");
    expect(tooltip()?.hidden).toBe(false);
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(tooltip()?.hidden).toBe(true);
  });

  it("shows nothing without a text", async () => {
    const host = mountHost(undefined).get("[data-testid=host]");
    await host.trigger("mouseenter");
    expect(tooltip()?.hidden ?? true).toBe(true);
    expect(host.attributes("aria-describedby")).toBeUndefined();
  });

  it("updates the text while shown and hides when the text goes away", async () => {
    const host = mountHost("first");
    await host.get("[data-testid=host]").trigger("mouseenter");
    await host.setProps({ text: "second" });
    expect(tooltip()?.textContent).toBe("second");
    await host.setProps({ text: undefined });
    expect(tooltip()?.hidden).toBe(true);
  });

  it("hides on a scroll and when the element is unmounted", async () => {
    const host = mountHost("value");
    await host.get("[data-testid=host]").trigger("mouseenter");
    document.dispatchEvent(new Event("scroll"));
    expect(tooltip()?.hidden).toBe(true);
    await host.get("[data-testid=host]").trigger("mouseenter");
    expect(tooltip()?.hidden).toBe(false);
    host.unmount();
    wrapper = null;
    expect(tooltip()?.hidden).toBe(true);
  });
});
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `npx vitest run tests/unit/tooltip.test.ts`
Expected: FAIL, `Failed to resolve import "@/directives/tooltip"`.

- [ ] **Step 4: Implement the directive**

`frontend/src/directives/tooltip.ts`:

```ts
import { computePosition, flip, offset, shift, type Placement } from "@floating-ui/dom";
import type { Directive, DirectiveBinding } from "vue";

/** The id of the one tooltip element of the application. */
export const TOOLTIP_ID = "app-tooltip";

type TooltipValue = string | null | undefined;

const PLACEMENTS = ["top", "bottom", "left", "right"] as const;

interface TooltipTarget {
  text: TooltipValue;
  placement: Placement;
  show: () => void;
  hide: () => void;
}

const targets = new WeakMap<HTMLElement, TooltipTarget>();
let tooltip: HTMLDivElement | null = null;
/** The element the tooltip is shown for. */
let owner: HTMLElement | null = null;

function tooltipElement(): HTMLDivElement {
  if (!tooltip?.isConnected) {
    tooltip = document.createElement("div");
    tooltip.id = TOOLTIP_ID;
    tooltip.setAttribute("role", "tooltip");
    tooltip.className =
      "fixed top-0 left-0 z-50 max-w-md rounded bg-gray-900 px-2 py-1 font-mono text-xs break-words text-white shadow";
    tooltip.hidden = true;
    document.body.appendChild(tooltip);
  }
  return tooltip;
}

function placementOf(binding: DirectiveBinding<TooltipValue>): Placement {
  return PLACEMENTS.find((placement) => binding.modifiers[placement]) ?? "top";
}

async function position(el: HTMLElement, placement: Placement): Promise<void> {
  const tip = tooltipElement();
  const { x, y } = await computePosition(el, tip, {
    strategy: "fixed",
    placement,
    middleware: [offset(4), flip(), shift({ padding: 8 })],
  });
  // the tooltip may have moved on to another element while the position was computed
  if (owner !== el) return;
  tip.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") hide();
}

function onScroll(): void {
  hide();
}

function show(el: HTMLElement): void {
  const target = targets.get(el);
  if (!target?.text) return;
  if (owner && owner !== el) owner.removeAttribute("aria-describedby");
  owner = el;
  const tip = tooltipElement();
  tip.textContent = target.text;
  tip.hidden = false;
  el.setAttribute("aria-describedby", TOOLTIP_ID);
  document.addEventListener("keydown", onKeydown);
  document.addEventListener("scroll", onScroll, { capture: true, passive: true });
  void position(el, target.placement);
}

/** Hide the tooltip; with an element only when it is shown for that element. */
function hide(el?: HTMLElement): void {
  if (el && owner !== el) return;
  if (tooltip) tooltip.hidden = true;
  owner?.removeAttribute("aria-describedby");
  owner = null;
  document.removeEventListener("keydown", onKeydown);
  document.removeEventListener("scroll", onScroll, { capture: true });
}

/** `v-tooltip.bottom="text"`: a tooltip on hover and keyboard focus, positioned with
 * Floating UI so that it stays in the viewport. An empty text shows no tooltip. */
export const vTooltip: Directive<HTMLElement, TooltipValue> = {
  mounted(el, binding) {
    const target: TooltipTarget = {
      text: binding.value,
      placement: placementOf(binding),
      show: () => show(el),
      hide: () => hide(el),
    };
    targets.set(el, target);
    el.addEventListener("mouseenter", target.show);
    el.addEventListener("focusin", target.show);
    el.addEventListener("mouseleave", target.hide);
    el.addEventListener("focusout", target.hide);
  },
  updated(el, binding) {
    const target = targets.get(el);
    if (!target) return;
    target.text = binding.value;
    target.placement = placementOf(binding);
    if (owner !== el) return;
    if (!target.text) {
      hide(el);
      return;
    }
    tooltipElement().textContent = target.text;
    void position(el, target.placement);
  },
  beforeUnmount(el) {
    const target = targets.get(el);
    if (target) {
      el.removeEventListener("mouseenter", target.show);
      el.removeEventListener("focusin", target.show);
      el.removeEventListener("mouseleave", target.hide);
      el.removeEventListener("focusout", target.hide);
      targets.delete(el);
    }
    hide(el);
  },
};
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `npx vitest run tests/unit/tooltip.test.ts`
Expected: PASS, 6 tests.

- [ ] **Step 6: Register the directive in the application and the tests**

In `frontend/src/main.ts` replace `import Tooltip from "primevue/tooltip";` by `import { vTooltip } from "@/directives/tooltip";` (placed with the other `@/` imports, after `import { primevueOptions } from "@/assets/primevue";`) and `app.directive("tooltip", Tooltip);` by `app.directive("tooltip", vTooltip);`.

In `frontend/tests/unit/inspector.test.ts`, `frontend/tests/unit/reportPage.test.ts` and `frontend/tests/unit/elementTable.test.ts` remove `import Tooltip from "primevue/tooltip";`, add `import { vTooltip } from "@/directives/tooltip";` to the `@/` imports and replace every `directives: { tooltip: Tooltip }` by `directives: { tooltip: vTooltip }`.

Run: `grep -rn "primevue/tooltip" src tests`
Expected: no output.

- [ ] **Step 7: Run all unit tests, lint, type check, commit**

```bash
npx prettier --write src/directives/tooltip.ts src/main.ts tests/unit/tooltip.test.ts tests/unit/inspector.test.ts tests/unit/reportPage.test.ts tests/unit/elementTable.test.ts
npx vitest run && npm run lint && npm run typecheck
git add package.json package-lock.json src/directives/tooltip.ts src/main.ts tests/unit
git commit -m "Replace the tooltip of PrimeVue by an own directive positioned with Floating UI"
```

Expected: all unit tests pass (the existing 109 plus the new ones).

---

### Task 4: Lucide icons

**Files:**
- Modify: `frontend/src/data/sbmlTypes.ts` (`icon: Component`, Lucide components)
- Modify: `frontend/src/components/misc/TypeMark.vue`
- Modify: `frontend/src/components/report/SearchBox.vue:28-30`
- Modify: `frontend/src/components/input/FileUpload.vue:28`
- Modify: `frontend/src/components/inspector/InspectorPanel.vue:71`
- Modify: `frontend/src/components/layout/LoadingState.vue:10`
- Modify: `frontend/src/components/misc/BooleanMark.vue:6`
- Modify: `frontend/src/assets/main.css:2` (remove the PrimeIcons import)
- Modify: `frontend/tests/unit/sbmlTypes.test.ts:43`
- Create: `frontend/tests/unit/icons.test.ts`
- Modify: `frontend/package.json`, `frontend/package-lock.json` (add `@lucide/vue`, remove `primeicons`)

**Interfaces:**
- Produces: `SbmlTypeInfo.icon: Component` (from `vue`), a Lucide icon component.

- [ ] **Step 1: Add the dependency**

```bash
npm install @lucide/vue@^1.47.0
```

- [ ] **Step 2: Write the failing test**

`frontend/tests/unit/icons.test.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import BooleanMark from "@/components/misc/BooleanMark.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import { DOCUMENT_TYPES, ELEMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";

describe("icons", () => {
  it("renders the svg icon of every type in both sizes", () => {
    for (const info of [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES]) {
      const small = mount(TypeMark, { props: { type: info.type } });
      const svg = small.get("svg");
      expect(svg.classes(), info.type).toContain("size-2.5");
      expect(svg.attributes("aria-hidden")).toBe("true");
      expect(small.attributes("title")).toBe(info.label);
      expect(mount(TypeMark, { props: { type: info.type, size: "md" } }).get("svg").classes()).toContain(
        "size-3.5",
      );
    }
    expect(mount(TypeMark, { props: { type: "Reaction" } }).get("svg").classes()).toContain(
      "lucide-arrow-right-left",
    );
  });

  it("labels the check mark of a true value", () => {
    const check = mount(BooleanMark, { props: { value: true } }).get("svg");
    expect(check.attributes("aria-label")).toBe("true");
    expect(check.attributes("role")).toBe("img");
    expect(check.attributes("aria-hidden")).toBeUndefined();
    expect(mount(BooleanMark, { props: { value: false } }).find("svg").exists()).toBe(false);
  });

  it("spins the loading icon", () => {
    const wrapper = mount(LoadingState, { props: { message: "Loading" } });
    expect(wrapper.get("svg").classes()).toContain("animate-spin");
  });
});
```

Run: `npx vitest run tests/unit/icons.test.ts`
Expected: FAIL, `Error: Unable to get svg` (the components still render `<i class="pi ...">`).

- [ ] **Step 3: Replace the icons of the types**

In `frontend/src/data/sbmlTypes.ts`:

1. Add at the top, before the existing `import type {...} from "@/api/types";`:

```ts
import {
  ActivityIcon,
  ArrowRightLeftIcon,
  BoxIcon,
  CalculatorIcon,
  CircleArrowLeftIcon,
  CircleDotIcon,
  CircleIcon,
  CircleQuestionMarkIcon,
  ClockIcon,
  CodeIcon,
  EqualIcon,
  ExternalLinkIcon,
  FileIcon,
  HashIcon,
  LayoutGridIcon,
  LockIcon,
  LogInIcon,
  NetworkIcon,
  SlidersHorizontalIcon,
  TagIcon,
  TargetIcon,
} from "@lucide/vue";
import type { Component } from "vue";
```

2. Replace in `SbmlTypeInfo`:

```ts
  /** PrimeIcons class without the `pi` prefix. */
  icon: string;
```

by

```ts
  /** The icon, a component of `@lucide/vue`. */
  icon: Component;
```

3. Replace the `icon` value of every entry (the strings become identifiers without quotes):

| type | old | new |
| --- | --- | --- |
| SBMLDocument | `"pi-file"` | `FileIcon` |
| Model | `"pi-sitemap"` | `NetworkIcon` |
| ExternalModelDefinition | `"pi-external-link"` | `ExternalLinkIcon` |
| FunctionDefinition | `"pi-code"` | `CodeIcon` |
| UnitDefinition | `"pi-calculator"` | `CalculatorIcon` |
| Compartment | `"pi-box"` | `BoxIcon` |
| Species | `"pi-circle"` | `CircleIcon` |
| Parameter | `"pi-sliders-h"` | `SlidersHorizontalIcon` |
| InitialAssignment | `"pi-arrow-circle-left"` | `CircleArrowLeftIcon` |
| AssignmentRule | `"pi-equals"` | `EqualIcon` |
| RateRule | `"pi-wave-pulse"` | `ActivityIcon` |
| AlgebraicRule | `"pi-hashtag"` | `HashIcon` |
| Constraint | `"pi-lock"` | `LockIcon` |
| Reaction | `"pi-arrow-right-arrow-left"` | `ArrowRightLeftIcon` |
| Event | `"pi-clock"` | `ClockIcon` |
| Submodel | `"pi-th-large"` | `LayoutGridIcon` |
| Port | `"pi-sign-in"` | `LogInIcon` |
| GeneProduct | `"pi-tag"` | `TagIcon` |
| Objective | `"pi-bullseye"` | `TargetIcon` |
| SpeciesReference | `"pi-circle-fill"` | `CircleDotIcon` |
| ModifierSpeciesReference | `"pi-circle"` | `CircleIcon` |
| KineticLaw | `"pi-calculator"` | `CalculatorIcon` |
| LocalParameter | `"pi-sliders-h"` | `SlidersHorizontalIcon` |
| EventAssignment | `"pi-equals"` | `EqualIcon` |
| Uncertainty | `"pi-question-circle"` | `CircleQuestionMarkIcon` |

Run: `grep -n '"pi-' src/data/sbmlTypes.ts`
Expected: no output.

4. In `frontend/tests/unit/sbmlTypes.test.ts` replace `expect(info.icon).toMatch(/^pi-/);` by `expect(info.icon, info.type).toBeDefined();` (the rendering is covered by `icons.test.ts`).

- [ ] **Step 4: Render the icon in TypeMark**

`frontend/src/components/misc/TypeMark.vue` template becomes (the text size classes are gone, the icon has an explicit size):

```vue
<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-sm text-gray-800"
    :class="size === 'sm' ? 'size-4' : 'size-6'"
    :style="{ backgroundColor: info.color }"
    :title="info.label"
    data-testid="type-mark"
  >
    <component :is="info.icon" :class="size === 'sm' ? 'size-2.5' : 'size-3.5'" />
  </span>
</template>
```

- [ ] **Step 5: Replace the other icons**

`frontend/src/components/report/SearchBox.vue`: add `import { SearchIcon } from "@lucide/vue";` as the first import and replace

```vue
    <i
      class="pi pi-search pointer-events-none absolute top-1/2 left-2 -translate-y-1/2 text-xs text-gray-400"
    />
```

by

```vue
    <SearchIcon
      class="pointer-events-none absolute top-1/2 left-2 size-3 -translate-y-1/2 text-gray-400"
    />
```

`frontend/src/components/input/FileUpload.vue`: add `import { UploadIcon } from "@lucide/vue";` as the first import and replace `<i class="pi pi-upload text-2xl text-gray-400" />` by `<UploadIcon class="size-6 text-gray-400" />`.

`frontend/src/components/inspector/InspectorPanel.vue`: add `import { XIcon } from "@lucide/vue";` as the first import and replace `<i class="pi pi-times text-xs" />` by `<XIcon class="size-3" />`.

`frontend/src/components/layout/LoadingState.vue` becomes:

```vue
<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";

defineProps<{ message: string }>();
</script>

<template>
  <div
    class="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-gray-600"
    data-testid="loading-state"
  >
    <LoaderCircleIcon class="size-6 animate-spin" />
    <p class="text-sm">{{ message }}</p>
  </div>
</template>
```

`frontend/src/components/misc/BooleanMark.vue` becomes:

```vue
<script setup lang="ts">
import { CheckIcon } from "@lucide/vue";

defineProps<{ value: boolean | null | undefined }>();
</script>

<template>
  <CheckIcon v-if="value === true" class="size-3 text-gray-700" role="img" aria-label="true" />
  <span v-else class="text-gray-400">-</span>
</template>
```

`frontend/src/assets/main.css`: delete the line `@import "primeicons/primeicons.css";`.

Remove the package:

```bash
npm uninstall primeicons
grep -rnE 'class="pi |"pi-|primeicons' src tests/unit tests/e2e index.html
```

Expected: the grep prints nothing.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `npx vitest run`
Expected: PASS, including the 3 tests of `icons.test.ts`. If a Lucide component does not accept `role` or `aria-label` as attributes, the check mark test shows it; the attributes fall through to the `<svg>` in `@lucide/vue` 1.47.

- [ ] **Step 7: Build, lint, type check, commit**

```bash
npx prettier --write src/data/sbmlTypes.ts src/components tests/unit/icons.test.ts tests/unit/sbmlTypes.test.ts
npm run lint && npm run typecheck && npm run build
ls dist/assets | grep -i primeicons
git add package.json package-lock.json src tests/unit
git commit -m "Replace PrimeIcons by the Lucide icons"
```

Expected: the build succeeds and `ls dist/assets | grep -i primeicons` prints nothing.

---

### Task 5: Native select of the archive entry and the model

**Files:**
- Create: `frontend/src/components/input/SelectInput.vue`
- Test: `frontend/tests/unit/selectInput.test.ts`
- Modify: `frontend/src/components/report/ContextBar.vue`
- Modify: `frontend/tests/e2e/report.spec.ts:65-80`

**Interfaces:**
- Consumes: `ChevronDownIcon` from `@lucide/vue` (added in Task 4).
- Produces: `SelectInput.vue` with `v-model: string` (prop `modelValue`, event `update:modelValue`), prop `options: readonly { label: string; value: string }[]`; attributes such as `data-testid` land on the `<select>`.

- [ ] **Step 1: Write the failing test**

`frontend/tests/unit/selectInput.test.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SelectInput from "@/components/input/SelectInput.vue";

const options = [
  { label: "./models/omex_minimal.xml", value: "./models/omex_minimal.xml" },
  { label: "m1 (definition)", value: "m1" },
];

describe("SelectInput", () => {
  it("renders the options with the selected value on the select", () => {
    const wrapper = mount(SelectInput, {
      props: { modelValue: "m1", options },
      attrs: { "data-testid": "model-select" },
    });
    const select = wrapper.get("select");
    expect(select.attributes("data-testid")).toBe("model-select");
    expect(wrapper.findAll("option").map((option) => option.text())).toEqual([
      "./models/omex_minimal.xml",
      "m1 (definition)",
    ]);
    expect((select.element as HTMLSelectElement).value).toBe("m1");
    expect(wrapper.get("svg").classes()).toContain("lucide-chevron-down");
  });

  it("emits the chosen value", async () => {
    const wrapper = mount(SelectInput, {
      props: { modelValue: "./models/omex_minimal.xml", options },
    });
    await wrapper.get("select").setValue("m1");
    expect(wrapper.emitted("update:modelValue")).toEqual([["m1"]]);
  });

  it("follows a new model value", async () => {
    const wrapper = mount(SelectInput, {
      props: { modelValue: "./models/omex_minimal.xml", options },
    });
    await wrapper.setProps({ modelValue: "m1" });
    expect((wrapper.get("select").element as HTMLSelectElement).value).toBe("m1");
  });
});
```

Run: `npx vitest run tests/unit/selectInput.test.ts`
Expected: FAIL, `Failed to resolve import "@/components/input/SelectInput.vue"`.

- [ ] **Step 2: Implement SelectInput**

`frontend/src/components/input/SelectInput.vue`:

```vue
<script setup lang="ts">
import { ChevronDownIcon } from "@lucide/vue";

// the attributes (data-testid, aria-label) belong to the select, not to the wrapper
defineOptions({ inheritAttrs: false });

defineProps<{ options: readonly { label: string; value: string }[] }>();
const model = defineModel<string>({ required: true });
</script>

<template>
  <span class="relative inline-flex items-center">
    <select
      v-bind="$attrs"
      v-model="model"
      class="max-w-72 cursor-pointer appearance-none truncate rounded border border-gray-300 bg-white py-1 pr-7 pl-2 text-sm hover:border-gray-400 focus:border-link focus:outline-none"
    >
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <ChevronDownIcon class="pointer-events-none absolute right-2 size-3 text-gray-500" />
  </span>
</template>
```

Run: `npx vitest run tests/unit/selectInput.test.ts`
Expected: PASS, 3 tests.

- [ ] **Step 3: Use it in the context bar**

In `frontend/src/components/report/ContextBar.vue` replace `import Select from "primevue/select";` by `import SelectInput from "@/components/input/SelectInput.vue";` (as the first `@/` import, the `vue` import stays above it) and replace the two `<Select ... />` elements by:

```vue
    <SelectInput
      v-if="entries.length > 1"
      :model-value="entry"
      :options="entryOptions"
      data-testid="entry-select"
      @update:model-value="(value: string) => view.setEntry(value)"
    />
```

and

```vue
    <SelectInput
      v-if="index.models.length > 1"
      :model-value="model.id ?? ''"
      :options="modelOptions"
      data-testid="model-select"
      @update:model-value="(value: string) => view.setModel(value)"
    />
```

- [ ] **Step 4: Update the end to end tests of the dropdowns**

A native select fires no change for the option which is already selected, and the archive opens on `./models/omex_minimal.xml`, so the test switches to another entry (`./models/omex_comp.xml` has the single model `omex_comp`). In `frontend/tests/e2e/report.spec.ts` replace the two tests at the end of the file by:

```ts
test("the archive dropdown switches the entry", async ({ page }) => {
  await openExample(page, "CompModels");
  const select = page.getByTestId("entry-select");
  await expect(select).toHaveValue("./models/omex_minimal.xml");
  await select.selectOption("./models/omex_comp.xml");
  await expect(page.getByTestId("model-name")).toHaveText("omex_comp");
  expect(query(page, "entry")).toBe("./models/omex_comp.xml");
});

test("the model dropdown switches to a model definition", async ({ page }) => {
  await openExample(page, "model_definitions (model_definitions.xml)");
  await page.getByTestId("model-select").selectOption("m1");
  await expect(page.getByTestId("rail-model")).toContainText("m1");
  expect(query(page, "model")).toBe("m1");
});
```

- [ ] **Step 5: Run the unit and the end to end tests**

```bash
npx vitest run
CI=1 npx playwright test tests/e2e/report.spec.ts --project=chromium
```

Expected: all unit tests pass; the 6 tests of `report.spec.ts` pass.

- [ ] **Step 6: Lint, type check, commit**

```bash
npx prettier --write src/components/input/SelectInput.vue src/components/report/ContextBar.vue tests/unit/selectInput.test.ts tests/e2e/report.spec.ts
npm run lint && npm run typecheck
git add src/components/input/SelectInput.vue src/components/report/ContextBar.vue tests/unit/selectInput.test.ts tests/e2e/report.spec.ts
git commit -m "Replace the select of PrimeVue by a native select in the context bar"
```

---

### Task 6: Own element table

**Files:**
- Modify (rewrite): `frontend/src/components/report/ElementTable.vue`
- Modify (rewrite the table tests, keep the `ElementCell` tests): `frontend/tests/unit/elementTable.test.ts`

**Interfaces:**
- Consumes: `sortRows`, `SortState` from `@/report/sort` (Task 1); `rowWindow` from `@/report/rowWindow` (Task 2); `vTooltip` from `@/directives/tooltip` (Task 3); `columnsOf`, `ColumnDef` from `@/report/columns`; `useReportView()` from `@/report/view` (`state.value.pk: string | null`, `select(pk: string | null): Promise<unknown>`); `ElementCell.vue` (props `row`, `column`).
- Produces: `ElementTable.vue` with the props `type: ElementType`, `rows: SbmlElement[]`; root `div` with `data-testid="table-<type>"`; rows `tr[data-pk]` with `aria-selected`; sortable header cells contain a `button[data-testid=sort-button]`; windowed tables have `[data-testid=virtual-cell]` wrappers and spacer rows `[data-testid=spacer-before]` / `[data-testid=spacer-after]`.

- [ ] **Step 1: Write the failing tests**

Replace the beginning of `frontend/tests/unit/elementTable.test.ts` (imports, the `ResizeObserverStub`, the fixtures and the two `describe` blocks `ElementTable` and `ElementTable virtual scrolling`) by the following; the `describe("ElementCell", ...)` block at the end of the file stays unchanged.

```ts
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { ref } from "vue";

import type { Parameter, Reaction, SbmlElement, Species } from "@/api/types";
import ElementCell from "@/components/report/ElementCell.vue";
import ElementTable from "@/components/report/ElementTable.vue";
import { vTooltip } from "@/directives/tooltip";
import { columnsOf, type ColumnDef } from "@/report/columns";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

/** The row height ElementTable pins a windowed row to. */
const ROW_HEIGHT = 36;

const index = new ReportIndex(loadReport("repressilator"));
const species = index.byType("BIOMD0000000012").get("Species") as Species[];
const icgBody = new ReportIndex(loadReport("icg_body"));

let wrapper: ReturnType<typeof mount> | null = null;

function mountTable(rows: SbmlElement[]) {
  wrapper = mount(ElementTable, {
    props: { type: "Species", rows },
    attachTo: document.body,
    global: {
      plugins: [router],
      directives: { tooltip: vTooltip },
      provide: { [ReportIndexKey as symbol]: ref(index) },
    },
  });
  return wrapper;
}

const header = (table: ReturnType<typeof mount>, title: string) =>
  table.findAll("thead th").find((th) => th.text() === title)!;
const ids = (table: ReturnType<typeof mount>) =>
  table.findAll("tbody tr[data-pk]").map((row) => row.find("td").text());
const nextFrame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
});

describe("ElementTable", () => {
  it("renders a row per element with the id, a compartment link and marks", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    expect(table.attributes("data-testid")).toBe("table-Species");
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows).toHaveLength(species.length);
    expect(rows[0]!.attributes("data-pk")).toBe(species[0]!.pk);
    expect(rows[0]!.text()).toContain(species[0]!.id);
    const link = rows[0]!.find("[data-testid=element-link]");
    expect(link.exists()).toBe(true);
    expect(link.text()).toBe(species[0]!.compartment);
    expect(table.findAll("thead th").map((th) => th.text())).toContain("compartment");
  });

  it("sorts by a click on the header and toggles the order", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    expect(ids(table)).toEqual(["PX", "PY", "PZ", "X", "Y", "Z"]);
    expect(header(table, "id").attributes("aria-sort")).toBe("none");

    await header(table, "id").get("[data-testid=sort-button]").trigger("click");
    expect(header(table, "id").attributes("aria-sort")).toBe("ascending");
    expect(ids(table)).toEqual(["PX", "PY", "PZ", "X", "Y", "Z"]);

    await header(table, "id").get("[data-testid=sort-button]").trigger("click");
    expect(header(table, "id").attributes("aria-sort")).toBe("descending");
    expect(ids(table)).toEqual(["Z", "Y", "X", "PZ", "PY", "PX"]);

    // another column starts ascending, equal values keep the order of the report
    await header(table, "initial amount").get("[data-testid=sort-button]").trigger("click");
    expect(header(table, "id").attributes("aria-sort")).toBe("none");
    expect(header(table, "initial amount").attributes("aria-sort")).toBe("ascending");
    expect(ids(table)).toEqual(["PX", "PY", "PZ", "X", "Z", "Y"]);
  });

  it("has no sort for the units columns", async () => {
    await router.push("/examples/BIOMD0000000012");
    const derived = header(mountTable(species), "derived units");
    expect(derived.find("[data-testid=sort-button]").exists()).toBe(false);
    expect(derived.attributes("aria-sort")).toBeUndefined();
  });

  it("selects a row by a click and clears the selection by a second click", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    await table.findAll("tbody tr[data-pk]")[1]!.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(species[1]!.pk);
    const selected = table.findAll("tbody tr[data-pk]")[1]!;
    expect(selected.attributes("aria-selected")).toBe("true");
    expect(selected.classes()).toContain("bg-selected");

    await selected.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBeUndefined();
    expect(table.findAll("tbody tr[data-pk]")[1]!.attributes("aria-selected")).toBe("false");
  });

  it("follows a link in a cell without selecting the row", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    const link = table.findAll("tbody tr[data-pk]")[0]!.get("[data-testid=element-link]");
    await link.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(link.attributes("data-pk"));
    expect(router.currentRoute.value.query.pk).not.toBe(species[0]!.pk);
  });

  it("moves the focus with the arrow keys and selects with Enter", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows.map((row) => row.attributes("tabindex"))).toEqual(["0", "-1", "-1", "-1", "-1", "-1"]);
    (rows[0]!.element as HTMLElement).focus();
    await rows[0]!.trigger("keydown", { key: "ArrowDown" });
    await flushPromises();
    expect(document.activeElement).toBe(table.findAll("tbody tr[data-pk]")[1]!.element);
    await table.findAll("tbody tr[data-pk]")[1]!.trigger("keydown", { key: "Enter" });
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(species[1]!.pk);
    expect(table.findAll("tbody tr[data-pk]")[1]!.attributes("tabindex")).toBe("0");
  });
});

describe("ElementTable windowing", () => {
  /** More rows than the threshold of 200, with a pk of their own. */
  const many = Array.from({ length: 1000 }, (_, i) => ({ ...species[0]!, pk: `virtual:${i}` }));

  it("renders only the rows in view of a table above 200 rows", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(many);
    expect((table.element as HTMLElement).style.height).toBe(`${ROW_HEIGHT * 15}px`);
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows).toHaveLength(20);
    expect(rows[0]!.attributes("data-pk")).toBe("virtual:0");
    expect(table.find("[data-testid=spacer-before]").exists()).toBe(false);
    expect(
      (table.get("[data-testid=spacer-after] td").element as HTMLElement).style.height,
    ).toBe(`${980 * ROW_HEIGHT}px`);
    expect(table.findAll("[data-testid=virtual-cell]").length).toBeGreaterThan(0);
  });

  it("renders the rows of the scroll position", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(many);
    (table.element as HTMLElement).scrollTop = ROW_HEIGHT * 500;
    await table.trigger("scroll");
    await nextFrame();
    await flushPromises();
    const rows = table.findAll("tbody tr[data-pk]");
    expect(rows[0]!.attributes("data-pk")).toBe("virtual:495");
    expect(rows).toHaveLength(25);
    expect(
      (table.get("[data-testid=spacer-before] td").element as HTMLElement).style.height,
    ).toBe(`${495 * ROW_HEIGHT}px`);
    expect(
      (table.get("[data-testid=spacer-after] td").element as HTMLElement).style.height,
    ).toBe(`${480 * ROW_HEIGHT}px`);
  });

  it("renders a short table without windowing and with natural rows", async () => {
    await router.push("/examples/BIOMD0000000012");
    const table = mountTable(species);
    expect((table.element as HTMLElement).style.height).toBe("");
    expect(table.find("[data-testid=virtual-cell]").exists()).toBe(false);
    expect(table.find("[data-testid=spacer-after]").exists()).toBe(false);
    expect(table.findAll("tbody tr[data-pk]")).toHaveLength(species.length);
  });
});
```

In the remaining `describe("ElementCell", ...)` block nothing changes except that it uses `vTooltip` (done in Task 3). The imports `Parameter`, `Reaction`, `ElementCell`, `columnsOf`, `ColumnDef` and `icgBody` are used by that block.

Run: `npx vitest run tests/unit/elementTable.test.ts`
Expected: FAIL: the PrimeVue table has no `sort-button`, no `aria-sort`, no spacer rows, and without the PrimeVue plugin it does not render.

- [ ] **Step 2: Implement the table**

`frontend/src/components/report/ElementTable.vue` (whole file):

```vue
<script setup lang="ts">
import {
  ArrowDownWideNarrowIcon,
  ArrowUpDownIcon,
  ArrowUpNarrowWideIcon,
} from "@lucide/vue";
import { computed, nextTick, onBeforeUnmount, ref, type Component } from "vue";

import type { ElementType, SbmlElement } from "@/api/types";
import ElementCell from "@/components/report/ElementCell.vue";
import { columnsOf, type ColumnDef } from "@/report/columns";
import { rowWindow } from "@/report/rowWindow";
import { sortRows, type SortState } from "@/report/sort";
import { useReportView } from "@/report/view";

/** A table with more rows renders only the rows in view. */
const VIRTUAL_ROWS = 200;
/** The height of a windowed row. The window places every row at `index * ROW_HEIGHT`, so
 * the row has to be exactly this high; a cell with a one line KaTeX fraction measures
 * 34 px, which leaves the 36 px of the row without clipping it. */
const ROW_HEIGHT = 36;
/** The rows a windowed table shows at once. */
const VIEWPORT_ROWS = 15;
/** The rows rendered above and below the viewport of a windowed table. */
const OVERSCAN = 5;
/** A click on these elements of a row does not change the selection. */
const INTERACTIVE = "a, button, input, select, textarea, [contenteditable]";

const props = defineProps<{ type: ElementType; rows: SbmlElement[] }>();
const view = useReportView();

const columns = computed(() => columnsOf(props.type));
const sort = ref<SortState | null>(null);
const sorted = computed(() => sortRows(props.rows, sort.value));
const virtual = computed(() => props.rows.length > VIRTUAL_ROWS);
const selectedPk = computed(() => view.state.value.pk);

const scroller = ref<HTMLElement | null>(null);
const scrollTop = ref(0);
let frame = 0;

/** One update of the window per animation frame. */
function onScroll(): void {
  if (!virtual.value || frame) return;
  frame = requestAnimationFrame(() => {
    frame = 0;
    scrollTop.value = scroller.value?.scrollTop ?? 0;
  });
}

onBeforeUnmount(() => cancelAnimationFrame(frame));

const range = computed(() =>
  virtual.value
    ? rowWindow(
        scrollTop.value,
        sorted.value.length,
        ROW_HEIGHT,
        ROW_HEIGHT * VIEWPORT_ROWS,
        OVERSCAN,
      )
    : { start: 0, end: sorted.value.length, before: 0, after: 0 },
);
const visible = computed(() => sorted.value.slice(range.value.start, range.value.end));

function sortable(column: ColumnDef): boolean {
  return column.kind !== "math" && column.kind !== "units";
}

function toggleSort(column: ColumnDef): void {
  sort.value =
    sort.value?.field === column.field
      ? { field: column.field, order: sort.value.order === 1 ? -1 : 1 }
      : { field: column.field, order: 1 };
}

function ariaSort(column: ColumnDef): "ascending" | "descending" | "none" | undefined {
  if (!sortable(column)) return undefined;
  if (sort.value?.field !== column.field) return "none";
  return sort.value.order === 1 ? "ascending" : "descending";
}

function sortIcon(column: ColumnDef): Component {
  if (sort.value?.field !== column.field) return ArrowUpDownIcon;
  return sort.value.order === 1 ? ArrowUpNarrowWideIcon : ArrowDownWideNarrowIcon;
}

function toggleSelection(row: SbmlElement): void {
  void view.select(row.pk === selectedPk.value ? null : row.pk);
}

function onRowClick(event: MouseEvent, row: SbmlElement): void {
  if ((event.target as Element | null)?.closest(INTERACTIVE)) return;
  toggleSelection(row);
}

/** The row the keyboard focus last moved to. */
const activePk = ref<string | null>(null);
const rowElements = new Map<string, HTMLElement>();

/** The one row reachable by tab: the last focused row, else the selected row, else the
 * first row, each only when it is rendered. */
const tabbablePk = computed(() => {
  const rendered = new Set(visible.value.map((row) => row.pk));
  for (const pk of [activePk.value, selectedPk.value]) {
    if (pk && rendered.has(pk)) return pk;
  }
  return visible.value[0]?.pk ?? null;
});

function setRowElement(pk: string, element: unknown): void {
  if (element instanceof HTMLElement) rowElements.set(pk, element);
  else rowElements.delete(pk);
}

async function onRowKeydown(event: KeyboardEvent, row: SbmlElement, index: number): Promise<void> {
  // keys on a link or another control inside the row are theirs
  if (event.target !== event.currentTarget) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const next = sorted.value[index + (event.key === "ArrowDown" ? 1 : -1)];
    if (!next) return;
    activePk.value = next.pk;
    await nextTick();
    const element = rowElements.get(next.pk);
    element?.focus({ preventScroll: true });
    // jsdom has no scrollIntoView
    element?.scrollIntoView?.({ block: "nearest" });
  } else if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    toggleSelection(row);
  }
}
</script>

<template>
  <div
    ref="scroller"
    class="overflow-auto"
    :style="virtual ? { height: `${ROW_HEIGHT * VIEWPORT_ROWS}px` } : undefined"
    :data-testid="`table-${type}`"
    @scroll.passive="onScroll"
  >
    <table class="w-full border-collapse text-sm">
      <thead class="sticky top-0 z-10 bg-gray-50">
        <tr class="border-b border-gray-200">
          <th
            v-for="column in columns"
            :key="column.field"
            scope="col"
            class="px-3 py-2 text-left font-medium whitespace-nowrap text-gray-600 select-none"
            :style="column.width ? { width: column.width } : undefined"
            :aria-sort="ariaSort(column)"
          >
            <button
              v-if="sortable(column)"
              type="button"
              class="flex cursor-pointer items-center gap-1 rounded-sm font-medium focus-visible:outline-2 focus-visible:outline-link"
              data-testid="sort-button"
              @click="toggleSort(column)"
            >
              <span>{{ column.header }}</span>
              <component :is="sortIcon(column)" class="size-3 text-gray-400" />
            </button>
            <span v-else class="flex items-center gap-1">{{ column.header }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="range.before > 0" aria-hidden="true" data-testid="spacer-before">
          <td :colspan="columns.length" class="p-0" :style="{ height: `${range.before}px` }" />
        </tr>
        <tr
          v-for="(row, i) in visible"
          :key="row.pk"
          :ref="(element) => setRowElement(row.pk, element)"
          :data-pk="row.pk"
          :aria-selected="row.pk === selectedPk"
          :tabindex="row.pk === tabbablePk ? 0 : -1"
          class="cursor-pointer border-b border-gray-100 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-link"
          :class="[row.pk === selectedPk ? 'bg-selected' : 'hover:bg-gray-50', { 'scroll-mt-10': virtual }]"
          @click="onRowClick($event, row)"
          @keydown="onRowKeydown($event, row, range.start + i)"
          @focus="activePk = row.pk"
        >
          <td
            v-for="column in columns"
            :key="column.field"
            class="px-3 align-top whitespace-nowrap"
            :class="virtual ? 'py-0' : 'py-1.5'"
            :style="column.width ? { width: column.width } : undefined"
          >
            <div
              v-if="virtual"
              class="flex items-center overflow-hidden"
              :style="{ height: `${ROW_HEIGHT - 1}px` }"
              data-testid="virtual-cell"
            >
              <ElementCell :row="row" :column="column" />
            </div>
            <ElementCell v-else :row="row" :column="column" />
          </td>
        </tr>
        <tr v-if="range.after > 0" aria-hidden="true" data-testid="spacer-after">
          <td :colspan="columns.length" class="p-0" :style="{ height: `${range.after}px` }" />
        </tr>
      </tbody>
    </table>
  </div>
</template>
```

Notes for the implementation:
- The sticky header covers the top of the viewport of a windowed table; `scroll-mt-10` on the rows keeps a row which the arrow keys scroll into view below it.
- `onScroll` reads the `scrollTop` of the root `div` (`scroller`); a short table never updates the window.
- If `vue-tsc` rejects the function ref `:ref="(element) => setRowElement(row.pk, element)"`, type the parameter as `(element: Element | ComponentPublicInstance | null)` with `import type { ComponentPublicInstance } from "vue"`.

- [ ] **Step 3: Run the tests to verify they pass**

Run: `npx vitest run tests/unit/elementTable.test.ts`
Expected: PASS, the 6 `ElementTable`, 3 `ElementTable windowing` and 4 `ElementCell` tests.

- [ ] **Step 4: Run all unit tests and the end to end tests**

```bash
npx vitest run
CI=1 npx playwright test
```

Expected: all unit tests pass; all 13 end to end tests pass, including the walk over every example (about 2 minutes).

- [ ] **Step 5: Lint, type check, commit**

```bash
npx prettier --write src/components/report/ElementTable.vue tests/unit/elementTable.test.ts
npm run lint && npm run typecheck
git add src/components/report/ElementTable.vue tests/unit/elementTable.test.ts
git commit -m "Replace the DataTable of PrimeVue by an own table with sorting, selection and windowing"
```

---

### Task 7: Remove PrimeVue, split KaTeX, new end to end tests, documentation

**Files:**
- Modify: `frontend/src/main.ts` (remove the PrimeVue plugin)
- Delete: `frontend/src/assets/primevue.ts`
- Modify: `frontend/tests/unit/inspector.test.ts`, `frontend/tests/unit/reportPage.test.ts` (no PrimeVue plugin, no `ResizeObserver` stub)
- Modify: `frontend/package.json`, `frontend/package-lock.json` (remove `primevue`)
- Modify: `frontend/vite.config.ts` (only if the chunk of the report page stays above 500 kB)
- Modify: `frontend/tests/e2e/report.spec.ts` (sort and tooltip tests)
- Modify: `README.md:11`, `frontend/README.md:53`, `CLAUDE.md:9`, `CLAUDE.md:68`

**Interfaces:**
- Consumes: everything of Tasks 1 to 6. After this task no file imports `primevue`.

- [ ] **Step 1: Remove PrimeVue from the application and the tests**

`frontend/src/main.ts` becomes:

```ts
import { createPinia } from "pinia";
import { createApp } from "vue";
import { createGtag } from "vue-gtag";

import App from "@/App.vue";
import { vTooltip } from "@/directives/tooltip";
import { router } from "@/router";
import "@/assets/main.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.directive("tooltip", vTooltip);

if (import.meta.env.PROD) {
  app.use(createGtag({ tagId: "G-TZ6E25RS0Q", pageTracker: { router } }));
}

app.mount("#app");
```

```bash
git rm src/assets/primevue.ts
```

In `frontend/tests/unit/inspector.test.ts` remove `import PrimeVue from "primevue/config";` and `import { primevueOptions } from "@/assets/primevue";`, and replace both `plugins: [router, [PrimeVue, primevueOptions]],` by `plugins: [router],`.

In `frontend/tests/unit/reportPage.test.ts` remove `import PrimeVue from "primevue/config";`, `import { primevueOptions } from "@/assets/primevue";`, the comment `// jsdom has no ResizeObserver, ...`, the class `ResizeObserverStub` and the line `globalThis.ResizeObserver ??= ...`, and replace `plugins: [router, [PrimeVue, primevueOptions]],` by `plugins: [router],`.

```bash
npm uninstall primevue
grep -rni "primevue\|primeicons\|ResizeObserver" src tests package.json
npx vitest run
```

Expected: the grep prints nothing; all unit tests pass.

- [ ] **Step 2: Check the chunk size of the report page**

```bash
npm run build 2>&1 | grep -E "ReportPage|index-.*\.js|larger than 500"
```

If the output contains `Some chunks are larger than 500 kB`, give KaTeX a chunk of its own: in `frontend/vite.config.ts` add to the object passed to `defineConfig`, after `plugins`:

```ts
  build: {
    rolldownOptions: {
      output: {
        // KaTeX (about 270 kB) is a chunk of its own, so the chunk of the report page stays
        // below the warning limit of 500 kB and KaTeX is cached across releases
        codeSplitting: {
          groups: [{ name: "katex", test: /[\\/]node_modules[\\/]katex[\\/]/ }],
        },
      },
    },
  },
```

Run `npm run build` again. Expected: a `katex-*.js` chunk, no chunk above 500 kB and no `larger than 500 kB` warning. If the build rejects the option, read `node_modules/rolldown/dist/shared/define-config-*.d.mts` (search `codeSplitting`) for the shape of a group and adapt `name`/`test` to it. If the output had no warning, leave `vite.config.ts` unchanged.

- [ ] **Step 3: Add the end to end tests of sorting and the tooltip**

In `frontend/tests/e2e/report.spec.ts`, inside `test.describe("repressilator", ...)` after the test `the XML toggle shows the SBML of the element`, add:

```ts
  test("a click on a column header sorts the rows", async ({ page }) => {
    const table = page.getByTestId("table-Species");
    const ids = () => table.locator("tbody tr[data-pk] td:first-child").allInnerTexts();
    const sortById = table.getByRole("button", { name: "id", exact: true });
    const idHeader = table.locator("thead th").first();
    await sortById.click();
    await expect(idHeader).toHaveAttribute("aria-sort", "ascending");
    expect(await ids()).toEqual(["PX", "PY", "PZ", "X", "Y", "Z"]);
    await sortById.click();
    await expect(idHeader).toHaveAttribute("aria-sort", "descending");
    expect(await ids()).toEqual(["Z", "Y", "X", "PZ", "PY", "PX"]);
  });

  test("hovering a formula shows its tooltip below it", async ({ page }) => {
    const math = page.getByTestId("table-Reaction").getByTestId("math").first();
    // a scroll hides the tooltip: scroll first and let the scroll events pass before hovering
    await math.scrollIntoViewIfNeeded();
    await page.evaluate(
      () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))),
    );
    await math.hover();
    const tooltip = page.getByRole("tooltip");
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText("(click to copy)");
    const anchor = (await math.boundingBox())!;
    const box = (await tooltip.boundingBox())!;
    expect(box.y).toBeGreaterThanOrEqual(anchor.y + anchor.height);
    expect(box.y + box.height).toBeLessThanOrEqual(page.viewportSize()!.height);
    await page.mouse.move(0, 0);
    await expect(tooltip).toBeHidden();
  });
```

Run: `CI=1 npx playwright test`
Expected: all 15 tests pass.

- [ ] **Step 4: Update the documentation**

`README.md`, the row of `frontend/` in the repository layout, becomes:

```markdown
| `frontend/` | the Vue 3 application (Vite, TypeScript, Pinia, Vue Router, Tailwind CSS, Lucide icons) |
```

`frontend/README.md` line 53 becomes:

```markdown
- [Tailwind CSS](https://tailwindcss.com/) 4 for the styling with [Lucide](https://lucide.dev/) icons and [Floating UI](https://floating-ui.com/) for the tooltips; the tables, the dropdowns and the tooltip directive are components of the application. [KaTeX](https://katex.org/) renders the math and units, DOMPurify sanitises the notes.
```

`CLAUDE.md` line 9: replace `and PrimeVue 4 in unstyled mode with Tailwind CSS 4.` by `Tailwind CSS 4, Lucide icons (`@lucide/vue`) and Floating UI (`@floating-ui/dom`) for the tooltip; the element tables (sorting, selection, windowing above 200 rows), the dropdowns and the `v-tooltip` directive are own code.`

`CLAUDE.md` line 68: replace `; PrimeVue stays at `^4.5.5` (MIT, PrimeVue 5 is commercial).` by `. PrimeVue and PrimeIcons are not used: from PrimeVue 5 and PrimeIcons 8 on they are commercial (PrimeUI license); new dependencies have to be MIT, ISC or a comparable permissive license.`

Run: `grep -rni "primevue\|primeicons" README.md CLAUDE.md frontend/README.md`
Expected: only the sentence of `CLAUDE.md` line 68 which says that they are not used.

- [ ] **Step 5: Full verification**

```bash
npm run lint && npm run typecheck && npx vitest run && npm run build && npm audit && CI=1 npx playwright test
```

Expected: lint and type check clean, all unit tests pass, the build has no warning, `npm audit` finds 0 vulnerabilities, all 15 end to end tests pass.

- [ ] **Step 6: Commit**

```bash
npx prettier --write src/main.ts vite.config.ts tests/unit/inspector.test.ts tests/unit/reportPage.test.ts tests/e2e/report.spec.ts
npm run lint
git add -A src tests package.json package-lock.json vite.config.ts ../README.md ../CLAUDE.md README.md
git commit -m "Remove PrimeVue and document the stack without it"
```
