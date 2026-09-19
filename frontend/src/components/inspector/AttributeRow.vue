<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { attributeEntry } from "@/report/glossary";

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
</script>

<template>
  <!-- the label column holds the longest label of any type next to its value,
  `fbc:geneProductAssociation` of a reaction of an fbc model, which does not fit into 11rem; a
  longer one, the name of a list, labels a wide row and has the whole line -->
  <div
    class="grid gap-x-3 border-b border-gray-100 py-1 text-sm"
    :class="wide ? 'grid-cols-1' : 'grid-cols-[12rem_minmax(0,1fr)]'"
    data-testid="attribute-row"
  >
    <dt v-tooltip.bottom="tooltip" class="truncate text-gray-500">{{ name }}</dt>
    <dd class="min-w-0 break-words"><slot /></dd>
  </div>
</template>
