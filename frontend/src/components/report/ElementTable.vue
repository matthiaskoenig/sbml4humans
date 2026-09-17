<script setup lang="ts">
import { ArrowDownWideNarrowIcon, ArrowUpDownIcon, ArrowUpNarrowWideIcon } from "@lucide/vue";
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
