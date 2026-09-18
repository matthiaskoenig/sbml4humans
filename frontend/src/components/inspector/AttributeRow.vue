<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { attributeEntry } from "@/report/glossary";

const props = defineProps<{
  label: string;
  type?: SbmlType;
  field?: string;
  /** Puts the value below the label instead of next to it, so that it has the whole width of
   * the column. The rows which hold a table of their own use it: four columns of identifiers
   * do not fit next to a label column. */
  wide?: boolean;
}>();

const summary = computed(() =>
  props.type && props.field ? attributeEntry(props.type, props.field)?.summary : undefined,
);
/** A label longer than its column is truncated, so the tooltip repeats it in full before the
 * explanation, the way the native `title` of the label did. */
const tooltip = computed(() => (summary.value ? `${props.label}: ${summary.value}` : props.label));
</script>

<template>
  <!-- the label column holds the longest label of any type, `gene product association` of a
  reaction of an fbc model, which does not fit into 10rem -->
  <div
    class="grid gap-x-3 border-b border-gray-100 py-1 text-sm"
    :class="wide ? 'grid-cols-1' : 'grid-cols-[11rem_minmax(0,1fr)]'"
    data-testid="attribute-row"
  >
    <dt v-tooltip.bottom="tooltip" class="truncate text-gray-500">{{ label }}</dt>
    <dd class="min-w-0 break-words"><slot /></dd>
  </div>
</template>
