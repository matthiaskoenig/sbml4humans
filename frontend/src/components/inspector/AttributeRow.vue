<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import HelpLabel from "@/components/help/HelpLabel.vue";
import { attributeEntry, attributeKey } from "@/report/glossary";

const props = defineProps<{
  /** The type and the field of the glossary which name and explain the row. */
  type?: SbmlType;
  field?: string;
  /** The label of a row which the glossary does not name: a row without a field, and the one
   * row which shows a field of another type under a name of its own. */
  label?: string;
  /** Puts the value below the label instead of next to it, so that it has the whole width of
   * the column. The rows which hold a table of their own use it: four columns of identifiers
   * do not fit next to a label column. */
  wide?: boolean;
}>();

const entry = computed(() =>
  props.type && props.field ? attributeEntry(props.type, props.field) : undefined,
);
const name = computed(() => props.label ?? entry.value?.label ?? props.field ?? "");
/** A label longer than its column is truncated, so the tooltip repeats it in full before the
 * explanation, the way the native `title` of the label did. */
const tooltip = computed(() =>
  entry.value?.summary ? `${name.value}: ${entry.value.summary}` : name.value,
);
/** The entry the label opens, the attribute the row shows. A row without a field is named by the
 * caller and explained by nothing, and its label stays plain text. */
const helpKey = computed(() =>
  props.type && props.field ? attributeKey(props.type, props.field) : undefined,
);
</script>

<template>
  <!-- a row is a row of the grid of the attributes column: the label column of that grid is as
  wide as the longest label of the element, whatever the font is, so that no label is cut, neither
  `constant` nor `fbc:geneProductAssociation`, and the values of all rows start at one line. A wide
  row has the whole width for its label and for the table below it, and its label, the name of a
  list, does not widen the label column of the other rows -->
  <div
    class="col-span-2 grid gap-x-3 border-b border-gray-100 py-1 text-sm"
    :class="wide ? 'grid-cols-1' : 'grid-cols-subgrid'"
    data-testid="attribute-row"
  >
    <!-- the label is truncated by the cell around it and the link inside it is as wide as its
    text, so that the ellipsis stays and the visible label is what a reader clicks -->
    <dt class="truncate text-gray-500">
      <HelpLabel :help-key="helpKey" :tooltip="tooltip">{{ name }}</HelpLabel>
    </dt>
    <dd class="min-w-0 break-words"><slot /></dd>
  </div>
</template>
