<script setup lang="ts" generic="T extends object">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import HelpLabel from "@/components/help/HelpLabel.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { attributeEntry, attributeKey, attributeLabel } from "@/report/glossary";
import { useLimitedList } from "@/report/limitedList";

const props = defineProps<{
  rows: T[];
  /** The columns: the key of the cell and its slot, the attribute of the glossary which names
   * and explains the column where the key is not that attribute, a header for a column which
   * is not one attribute of the rows, and whether the column holds a double of the report,
   * which an infinite value reaches as a string. */
  columns: { key: string; header?: string; field?: string; double?: boolean }[];
  /** The type of the rows, whose attributes of the glossary explain the headers on hover. */
  type?: SbmlType;
  /** Widths in characters of the monospace font of the columns, for a table whose columns line
   * up with the same columns of the tables above and below it: the reactants, the products and
   * the modifiers of a reaction, the inputs and the outputs of a transition, the measures of the
   * uncertainties of an element. The table then lays its columns out by these widths, a column
   * without one is as wide as its header, and an empty column at the end takes what is left, so
   * that no column is wider in one table than in another. */
  widths?: Partial<Record<string, number>>;
}>();

function cell(row: T, key: string): string | number | null {
  const value = (row as Record<string, unknown>)[key];
  return typeof value === "string" || typeof value === "number" ? value : null;
}

/** The columns under their headers: the name the glossary gives the attribute of the column,
 * as a row of the inspector and a column of an element table are named. */
const headed = computed(() =>
  props.columns.map((column) => ({
    ...column,
    header:
      column.header ??
      (props.type ? attributeLabel(props.type, column.field ?? column.key) : column.key),
  })),
);

/** The header with the explanation of its attribute, the way the label of an attribute row
 * shows it. */
function tooltip(column: { header: string; key: string; field?: string }): string | undefined {
  if (!props.type) return undefined;
  const summary = attributeEntry(props.type, column.field ?? column.key)?.summary;
  return summary ? `${column.header}: ${summary}` : undefined;
}

/** The entry the header opens, the attribute of its column; a table whose rows are no type of
 * the report, the one a caller heads itself, explains nothing. */
function helpKey(column: { key: string; field?: string }): string | undefined {
  return props.type ? attributeKey(props.type, column.field ?? column.key) : undefined;
}

/** The width of a column of `chars` characters: a character of the monospace font is 0.6 of
 * its size wide, and the cell has the 0.75rem of padding at its right. */
function width(column: { key: string; header: string }): Record<string, string> {
  const chars = props.widths?.[column.key] ?? column.header.length;
  return { width: `calc(${(chars * 0.61).toFixed(2)}em + 0.75rem)` };
}

const { shown, hiddenCount, showAll } = useLimitedList(() => props.rows);
</script>

<template>
  <p v-if="rows.length === 0" class="text-gray-400">-</p>
  <template v-else>
    <!-- a table of four columns of identifiers is wider than the pane of the inspector on a
    narrow screen, and it scrolls there instead of being cut off at the edge of the pane -->
    <div class="overflow-x-auto">
      <table class="w-full text-xs" :class="{ 'table-fixed': widths }" data-testid="nested-table">
        <colgroup v-if="widths">
          <col v-for="column in headed" :key="column.key" :style="width(column)" />
          <col />
        </colgroup>
        <thead>
          <tr class="border-b border-gray-200 text-left text-gray-500">
            <th v-for="column in headed" :key="column.key" class="py-1 pr-3 font-medium">
              <HelpLabel :help-key="helpKey(column)" :tooltip="tooltip(column)">{{
                column.header
              }}</HelpLabel>
            </th>
            <th v-if="widths" aria-hidden="true" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in shown" :key="i" class="border-b border-gray-100 align-top">
            <!-- `break-words` only breaks inside a word when the word does not fit a line of its
          own, and it leaves the minimum width of a column at the width of its longest word, so
          the automatic layout gives an identifier the column it needs instead of wrapping
          `M_atp_c` into `M_at` and `p_c`. -->
            <td v-for="column in columns" :key="column.key" class="py-1 pr-3 break-words">
              <slot :name="`cell-${column.key}`" :row="row">
                <ValueText :value="cell(row, column.key)" :double="column.double" />
              </slot>
            </td>
            <td v-if="widths" aria-hidden="true" />
          </tr>
        </tbody>
      </table>
    </div>
    <ShowAllButton v-if="hiddenCount > 0" :count="hiddenCount" class="mt-1" @click="showAll" />
  </template>
</template>
