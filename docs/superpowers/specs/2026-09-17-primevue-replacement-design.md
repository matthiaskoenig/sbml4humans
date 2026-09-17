# Replacement of PrimeVue and PrimeIcons

Date: 2026-09-17. Status: approved design. Follows the frontend redesign of `2026-09-16-frontend-redesign-design.md`.

## Goal

Remove `primevue` and `primeicons` from the frontend and replace what the application uses of them by its own components and MIT or ISC licensed packages, with the same behaviour and the same look.

PrimeVue 5 and PrimeIcons 8 are no longer MIT licensed. They are part of the commercial "PrimeUI" family: a license key is required (the free Community License has to be renewed every year), a missing key may show a license notice, and the terms forbid decompiling the compiled package. The redesign pinned PrimeVue to 4.5.5, the last MIT release, which gets no further releases, but installed PrimeIcons 8.0.1, which is already under the new license.

## Non-goals

- No change of the layout, the colours or the behaviour of the report page beyond what is listed here.
- No new table features (filtering per column, multi column sort, column resizing, sticky first column).
- Column widths of a windowed table follow the rows in view, as they did with PrimeVue; fixed column widths are a separate change.
- No touch specific tooltip behaviour.

## What PrimeVue provides today

| part | used in | replaced by |
| --- | --- | --- |
| `DataTable`, `Column` (sort, single selection, virtual scroller above 200 rows) | `components/report/ElementTable.vue` | own table, own windowing |
| `Select` | `components/report/ContextBar.vue` (archive entry, model) | `components/input/SelectInput.vue`, a native `<select>` |
| `Tooltip` directive | `MathView.vue`, `ValueText.vue`, `UnitsView.vue` | own `v-tooltip` directive with `@floating-ui/dom` |
| PrimeIcons (27 icons as `pi pi-*` classes) | `data/sbmlTypes.ts`, `TypeMark.vue`, `SearchBox.vue`, `FileUpload.vue`, `InspectorPanel.vue`, `LoadingState.vue`, `BooleanMark.vue` | `@lucide/vue` components |
| global configuration (`unstyled`, pass through classes) | `assets/primevue.ts`, `main.ts`, unit tests | classes in the templates |

The tooltip is broken today: the pass through classes are configured under `pt.tooltip`, which does not reach the directive, so the tooltip element is rendered without the `absolute` class below the viewport and nobody sees it. The replacement makes it visible.

## Dependencies

- Removed: `primevue` (with `@primevue/core`, `@primevue/icons`, `@primeuix/styled`, `@primeuix/styles`, `@primeuix/utils`) and `primeicons`.
- Added: `@lucide/vue` (ISC, no dependencies besides the `vue` peer) and `@floating-ui/dom` (MIT, with `@floating-ui/core` and `@floating-ui/utils`).
- Not used: `@tanstack/vue-virtual` and `@tanstack/vue-table` (the rows have a fixed height, the windowing is a few lines), `reka-ui` (about 20 packages for two dropdowns), `@iconify/tailwind4` (about 30 build time packages).

## Table

`ElementTable.vue` keeps its props (`type: ElementType`, `rows: SbmlElement[]`), its `data-testid="table-<type>"` and the `data-pk` of every row, so `ElementSection.vue`, the unit tests and the e2e tests keep their selectors.

### Markup and style

A native `<table class="w-full border-collapse text-sm">`. The classes of the PrimeVue pass through options move into the template unchanged:

- `thead`: `sticky top-0 z-10 bg-gray-50`, header row `border-b border-gray-200`
- header cell: `px-3 py-2 text-left font-medium text-gray-600 whitespace-nowrap select-none`, content `flex items-center gap-1`, sort icon `size-3 text-gray-400`
- body row: `cursor-pointer border-b border-gray-100`, selected `bg-selected`, otherwise `hover:bg-gray-50`
- body cell: `px-3 py-1.5 align-top whitespace-nowrap`
- a column with a `width` keeps it as inline style

### Sorting

- A column is sortable unless its kind is `math` or `units`, as today.
- The header of a sortable column is a `<button type="button">` (full cell content, no button styling) with the title and the sort icon. The `<th>` carries `aria-sort` (`ascending`, `descending`, `none` for the sortable columns without sort).
- One sort at a time, state `{ field, order: 1 | -1 } | null`, initially `null` (the order of the report). The first click on a column sorts ascending, every further click on the same column toggles the order, a click on another column sorts that one ascending.
- Icons: `ArrowUpDown` unsorted, `ArrowUpNarrowWide` ascending, `ArrowDownWideNarrow` descending.
- The comparison lives in `src/report/sort.ts` and has the semantics of PrimeVue 4 (`@primeuix/utils` `sort` with `nullSortOrder` 1): a value is empty when it is `null`, `undefined`, `""`, an empty array or an empty plain object; empty values sort last in both orders; two strings compare with `Intl.Collator(undefined, { numeric: true })`; other values compare with `<` and `>`. The values are read with `fieldValue` of `src/report/columns`. The sort is stable, a new `rows` prop (search, type toggles) is sorted with the current state.

### Selection

- The selected row is the row whose `pk` is `view.state.value.pk`, as today.
- A click on a row selects it (`view.select(pk)`), a click on the selected row clears the selection (`view.select(null)`).
- A click whose target is inside `a`, `button`, `input`, `select`, `textarea` or `[contenteditable]` of the row is ignored (`ElementLink` and `MathView` stop the propagation already, this keeps other controls safe).
- Keyboard: roving tabindex over the rows in view. The selected row has `tabindex="0"` when it is in view, otherwise the first row in view; all other rows `-1`. ArrowDown and ArrowUp move the focus to the next or previous row (in a windowed table the viewport scrolls to keep it visible), Enter and Space toggle the selection of the focused row. Rows carry `aria-selected`.
- A focused row shows a focus ring (`focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-link`).

### Windowing

- A table with more than 200 rows is windowed, a shorter one renders all rows with their natural height.
- A windowed table sits in a scroll container of `ROW_HEIGHT * 15` = 540 px height (`overflow-auto`), the header stays sticky inside it.
- Every row is exactly `ROW_HEIGHT` = 36 px high: the vertical padding of the cell moves into a wrapper `div` of 35 px (`flex items-center overflow-hidden`, `data-testid="virtual-cell"`), which clips content taller than one line; the 1 px bottom border completes the 36 px.
- `src/report/rowWindow.ts` exports a pure function `rowWindow(scrollTop, total, rowHeight, viewportHeight, overscan)` which returns `{ start, end, before, after }`: the index range `[start, end)` to render and the heights of a spacer row before and after it. The overscan is 5 rows on each side. The header height is not subtracted; the overscan covers it.
- The table renders a spacer `<tr aria-hidden="true">` with the height `before` (when above 0), the rows `start..end`, and a spacer with the height `after` (when above 0). The component tracks `scrollTop` of the container on `scroll` (passive listener, one update per animation frame).
- The heights are constants, there is no measuring and no `ResizeObserver`.

## Dropdown

`src/components/input/SelectInput.vue`:

- props `modelValue: string`, `options: { label: string; value: string }[]`; emits `update:modelValue` with the value of the chosen option; attributes (e.g. `data-testid`) fall through to the `<select>`
- a wrapper `span` (`relative inline-flex`) with the `<select>` (`appearance-none rounded border border-gray-300 bg-white py-1 pr-7 pl-2 text-sm hover:border-gray-400 cursor-pointer max-w-72 truncate`) and a `ChevronDown` icon (`pointer-events-none absolute right-2 size-3 text-gray-500`)
- `ContextBar.vue` uses it for the entry and the model with the options it computes today

The list of a native select is drawn by the browser.

## Tooltip

`src/directives/tooltip.ts` exports the directive `vTooltip`, registered globally as `tooltip` in `main.ts` and passed as `directives: { tooltip: vTooltip }` in the unit tests. The call sites keep `v-tooltip.bottom="text"`.

- The value is a string; `undefined`, `null` or an empty string means no tooltip.
- Placement from the modifier: `top`, `bottom`, `left` or `right`, default `top`.
- One shared element for the whole application, created on the first show and appended to `document.body`: `<div role="tooltip" id="app-tooltip">` with `fixed top-0 left-0 z-50 max-w-md rounded bg-gray-900 px-2 py-1 font-mono text-xs break-words text-white shadow`, `hidden` while not shown.
- Shown on `mouseenter` and `focusin` of the element, hidden on `mouseleave`, `focusout`, `Escape` (keydown on the document while shown), a `scroll` anywhere (capture) and when the element is unmounted or its value becomes empty while shown. While shown the element has `aria-describedby="app-tooltip"`.
- Position with `computePosition` of `@floating-ui/dom`: strategy `fixed`, the placement of the modifier, middleware `offset(4)`, `flip()`, `shift({ padding: 8 })`.
- An update of the value while the tooltip is shown for this element updates the text.

## Icons

`@lucide/vue` components, imported with the `Icon` suffix (`FileIcon`, `BoxIcon`, ...), so no import shadows a global such as `File`. `SbmlTypeInfo.icon` becomes a `Component`. The mapping (Lucide names without the suffix):

| type | PrimeIcons | Lucide |
| --- | --- | --- |
| SBMLDocument | `pi-file` | `File` |
| Model | `pi-sitemap` | `Network` |
| ExternalModelDefinition | `pi-external-link` | `ExternalLink` |
| FunctionDefinition | `pi-code` | `Code` |
| UnitDefinition, KineticLaw | `pi-calculator` | `Calculator` |
| Compartment | `pi-box` | `Box` |
| Species, ModifierSpeciesReference | `pi-circle` | `Circle` |
| SpeciesReference | `pi-circle-fill` | `CircleDot` |
| Parameter, LocalParameter | `pi-sliders-h` | `SlidersHorizontal` |
| InitialAssignment | `pi-arrow-circle-left` | `CircleArrowLeft` |
| AssignmentRule, EventAssignment | `pi-equals` | `Equal` |
| RateRule | `pi-wave-pulse` | `Activity` |
| AlgebraicRule | `pi-hashtag` | `Hash` |
| Constraint | `pi-lock` | `Lock` |
| Reaction | `pi-arrow-right-arrow-left` | `ArrowRightLeft` |
| Event | `pi-clock` | `Clock` |
| Submodel | `pi-th-large` | `LayoutGrid` |
| Port | `pi-sign-in` | `LogIn` |
| GeneProduct | `pi-tag` | `Tag` |
| Objective | `pi-bullseye` | `Target` |
| Uncertainty | `pi-question-circle` | `CircleQuestionMark` |

Other icons: `pi-search` `Search`, `pi-upload` `Upload`, `pi-times` `X`, `pi-spin pi-spinner` `LoaderCircle` with `animate-spin`, `pi-check` `Check`. The sizes follow the font sizes of the PrimeIcons they replace: `TypeMark` `size-2.5` (sm) and `size-3.5` (md), search, close and check `size-3`, upload and spinner `size-6`. Icons which are decoration get `aria-hidden="true"`, the check mark of `BooleanMark` keeps `aria-label="true"` with `role="img"`.

## Build

- `main.css` no longer imports `primeicons/primeicons.css`; the PrimeIcons fonts (about 650 kB of `eot`, `svg`, `ttf`, `woff`, `woff2`) leave `dist`.
- The chunk of the report page is 785 kB with PrimeVue, above the warning limit of 500 kB. After the replacement it is measured again; if it is still above the limit, KaTeX (about 270 kB) moves into a chunk of its own with `build.rolldownOptions.output.codeSplitting`, so the build has no warning.

## Testing

Unit tests (Vitest, jsdom):

- `sort.test.ts`: empty values last in both orders, numeric collation of strings (`x2` before `x10`), numbers, booleans, stability, nested fields.
- `rowWindow.test.ts`: the start, the middle and the end of the list, a list shorter than the viewport, the spacer heights add up to `total * rowHeight`.
- `elementTable.test.ts` (rewritten for the own table): a row per element with `data-pk`, header titles; sort by a click on the header with `aria-sort` and the order of the rows, toggle, another column; no sort button for math and units; selection by a click, deselection by a second click, a click on an element link does not select the row; keyboard ArrowDown, Enter; a windowed table renders only the window, the spacer heights and the rows after a scroll; a short table renders all rows without `virtual-cell`.
- `tooltip.test.ts`: shown with the text on `mouseenter` and `focusin`, `aria-describedby`, hidden on `mouseleave` and Escape, nothing for an empty value, text update while shown, hidden on unmount.
- `selectInput.test.ts`: the options, the selected value, `update:modelValue` on change.
- the existing tests which install PrimeVue (`inspector`, `reportPage`) register only the router and the directive.

End to end tests (Playwright):

- `report.spec.ts`: the dropdown tests use `selectOption`; new tests: a click on a column header sorts the rows (ascending, then descending), and hovering a formula shows a visible tooltip with the formula below it.
- the walk over every example stays as it is.

Visual check: the screenshots of the PrimeVue dependent parts (home, report page, sorted and selected tables, the inspector, a tooltip, the dropdowns, a windowed table at the top and scrolled) before and after the replacement, compared side by side.

## Documentation

README.md (repository layout) and CLAUDE.md describe the stack without PrimeVue: Vue 3, Vite, TypeScript, Pinia, Vue Router, Tailwind CSS, Lucide icons, Floating UI for the tooltip.
