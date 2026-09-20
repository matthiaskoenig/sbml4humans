<script setup lang="ts">
import { ArrowDownWideNarrowIcon, ArrowUpDownIcon, ArrowUpNarrowWideIcon } from "@lucide/vue";
import { computed, nextTick, onBeforeUnmount, ref, watch, type Component } from "vue";

import type { ElementType, SbmlElement } from "@/api/types";
import HelpButton from "@/components/help/HelpButton.vue";
import ElementCell from "@/components/report/ElementCell.vue";
import { fieldValue, visibleColumns, type ColumnDef } from "@/report/columns";
import { useReportIndex } from "@/report/context";
import { attributeEntry, attributeKey } from "@/report/glossary";
import { elementLabel } from "@/report/label";
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
/** The stroke of the 14 px sort icon (1.3 px): its glyph is 12 px wide and high, and the
 * `-mx-px` of the icon keeps its layout width at 12 px. */
const SORT_ICON_STROKE = 2.25;
/** A click on these elements of a row does not change the selection. */
const INTERACTIVE = "a, button, input, select, textarea, [contenteditable]";

const props = defineProps<{
  type: ElementType;
  rows: SbmlElement[];
  /** Every row of the type, which decides the optional columns; the rows of a search are a
   * part of it and would let a column come and go while a reader types. */
  allRows?: SbmlElement[];
}>();
const view = useReportView();
const index = useReportIndex();

const columns = computed(() => visibleColumns(props.type, props.allRows ?? props.rows));
const sort = ref<SortState | null>(null);

/** The value a row sorts by in a column: its field, and in the id column the name a row the
 * file gives no id is shown by. */
function sortValue(row: SbmlElement, field: string): unknown {
  const column = columns.value.find((c) => c.field === field);
  if (column?.kind === "id" && !row.id) return elementLabel(index.value, row.pk);
  return fieldValue(row, field);
}

const sorted = computed(() => sortRows(props.rows, sort.value, sortValue));
const virtual = computed(() => props.rows.length > VIRTUAL_ROWS);
const selectedPk = computed(() => view.state.value.pk);

const scroller = ref<HTMLElement | null>(null);
const scrollTop = ref(0);
let frame = 0;

/** One update of the window per animation frame. */
function onScroll(): void {
  if (frame) return;
  frame = requestAnimationFrame(() => {
    frame = 0;
    scrollTop.value = scroller.value?.scrollTop ?? 0;
  });
}

onBeforeUnmount(() => cancelAnimationFrame(frame));

/** The scroll position can drift when the table switches between windowed and short,
 * for example a search that thins the rows resets the scroll of the browser without a
 * scroll event we catch in time; resync it once the mode or the rows change instead of
 * trusting only the last scroll event. */
watch(
  [virtual, () => props.rows],
  () => {
    scrollTop.value = scroller.value?.scrollTop ?? 0;
  },
  { flush: "post" },
);

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

/** A column of rendered content has no order a reader could follow: the formulas and the units
 * have none, and a list of assignments would be compared as a list of objects, which leaves
 * every row equal and a sort that changes nothing under a header that promises one. */
function sortable(column: ColumnDef): boolean {
  return (
    column.kind !== "math" &&
    column.kind !== "units" &&
    column.kind !== "assignments" &&
    column.kind !== "terms" &&
    column.kind !== "elements" &&
    column.kind !== "geneAssociation" &&
    column.kind !== "influence" &&
    column.kind !== "functionTerms"
  );
}

/** The tooltip of a header: the summary of the attribute of the column. */
function headerTooltip(column: ColumnDef): string | undefined {
  return attributeEntry(props.type, column.field)?.summary;
}

/** The entry the help of a header opens, the attribute of its column. A column the glossary does
 * not name, which its tests rule out, gets no help rather than one which leads nowhere. */
function helpKey(column: ColumnDef): string | undefined {
  return attributeKey(props.type, column.field);
}

function toggleSort(column: ColumnDef): void {
  sort.value =
    sort.value?.field === column.field
      ? { field: column.field, order: sort.value.order === 1 ? -1 : 1 }
      : { field: column.field, order: 1 };
}

/** A click anywhere in the header cell sorts by its column. The button which carries the name is
 * what the keyboard reaches and what answers Enter and Space, and its click reaches this by
 * bubbling, so that the name and the cell around it are one target; the help link of the cell
 * keeps its click to itself and explains the column instead. */
function onHeaderClick(column: ColumnDef): void {
  if (sortable(column)) toggleSort(column);
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

/** The rows actually in view, without the overscan the render window adds around it; a
 * short table's viewport is every row it renders. */
const viewport = computed(() =>
  virtual.value
    ? rowWindow(scrollTop.value, sorted.value.length, ROW_HEIGHT, ROW_HEIGHT * VIEWPORT_ROWS, 0)
    : { start: 0, end: sorted.value.length, before: 0, after: 0 },
);

/** The one row reachable by tab: the row the keyboard focus last moved to when it is in
 * the viewport, else the selected row when it is in the viewport, else the first row in
 * the viewport. The overscan rows a windowed table renders around the viewport are never
 * tabbable on their own, so tabbing into a scrolled table cannot land above it. */
const tabbablePk = computed(() => {
  const inView = sorted.value.slice(viewport.value.start, viewport.value.end);
  const inViewPks = new Set(inView.map((row) => row.pk));
  for (const pk of [activePk.value, selectedPk.value]) {
    if (pk && inViewPks.has(pk)) return pk;
  }
  return inView[0]?.pk ?? null;
});

function setRowElement(pk: string, element: unknown): void {
  if (element instanceof HTMLElement) rowElements.set(pk, element);
  else rowElements.delete(pk);
}

/** Scrolls the windowed table so the row at `index` lies inside the viewport, moving the
 * render window (and so `rowElements`) with it before the caller awaits a tick. */
function scrollIndexIntoView(index: number): void {
  if (!virtual.value || !scroller.value) return;
  const viewportHeight = ROW_HEIGHT * VIEWPORT_ROWS;
  const rowTop = index * ROW_HEIGHT;
  const rowBottom = rowTop + ROW_HEIGHT;
  const viewTop = scroller.value.scrollTop;
  const viewBottom = viewTop + viewportHeight;
  if (rowTop < viewTop) scroller.value.scrollTop = rowTop;
  else if (rowBottom > viewBottom) scroller.value.scrollTop = rowBottom - viewportHeight;
  scrollTop.value = scroller.value.scrollTop;
}

async function onRowKeydown(event: KeyboardEvent, row: SbmlElement, index: number): Promise<void> {
  // keys on a link or another control inside the row are theirs
  if (event.target !== event.currentTarget) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const nextIndex = index + (event.key === "ArrowDown" ? 1 : -1);
    const next = sorted.value[nextIndex];
    if (!next) return;
    scrollIndexIntoView(nextIndex);
    await nextTick();
    const element = rowElements.get(next.pk);
    if (!element) return;
    activePk.value = next.pk;
    element.focus({ preventScroll: true });
    element.scrollIntoView({ block: "nearest" });
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
            class="group/th px-3 py-2 text-left font-medium whitespace-nowrap text-gray-600 select-none"
            :class="{ 'cursor-pointer': sortable(column) }"
            :style="column.width ? { width: column.width } : undefined"
            :aria-sort="ariaSort(column)"
            :aria-label="column.header"
            @click="onHeaderClick(column)"
          >
            <!-- the help of the column stands next to the name and never inside the button which
            carries it, so that the click which explains the column does not sort it and the
            keyboard reaches the two one after the other. The cell names itself, since the name of
            the help would otherwise be read out with the header of every cell of the column -->
            <!-- the row of the header is as wide as the name and the arrows, so that the help
            below stands after them wherever the column is wider than its header; in the last
            column it is the whole cell, so that the help ends at the edge of the table -->
            <div class="relative flex w-fit items-center gap-1 group-last/th:w-full">
              <button
                v-if="sortable(column)"
                v-tooltip.bottom="headerTooltip(column)"
                type="button"
                class="flex cursor-pointer items-center gap-1 rounded-sm font-medium focus-visible:outline-2 focus-visible:outline-link"
                data-testid="sort-button"
              >
                <span>{{ column.header }}</span>
                <component
                  :is="sortIcon(column)"
                  class="-mx-px size-3.5 text-gray-400"
                  :stroke-width="SORT_ICON_STROKE"
                />
              </button>
              <span
                v-else
                v-tooltip.bottom="headerTooltip(column)"
                class="flex items-center gap-1"
                >{{ column.header }}</span
              >
              <!-- the help costs the column no width: it is out of the flow, a step after the
              name of the column, in the 12 px of padding which part that name from the name of
              the next column, so that it covers neither of them and a dense table is as wide as
              it is without it. In the last column it stands at the edge of the cell instead, one
              step further left, since a step beyond it would be a step beyond the table, which
              would make the table scroll. It is shown when the cell is hovered or carries the
              focus, and always where there is no pointer which could hover it; the hit area
              around it is the square a finger needs, and it reaches to the left, over the cell,
              and never past the icon -->
              <HelpButton
                v-if="helpKey(column)"
                :help-key="helpKey(column)!"
                :label="column.header"
                size="sm"
                class="absolute top-1/2 left-full ml-1 -translate-y-1/2 opacity-0 before:absolute before:-inset-y-1 before:right-0 before:-left-2 group-last/th:ml-0 group-focus-within/th:opacity-100 group-hover/th:opacity-100 pointer-coarse:opacity-100"
              />
            </div>
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
          :class="[
            row.pk === selectedPk ? 'bg-selected' : 'hover:bg-gray-50',
            { 'scroll-mt-10': virtual },
          ]"
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
