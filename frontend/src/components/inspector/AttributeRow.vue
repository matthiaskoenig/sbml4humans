<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { attributeEntry } from "@/report/glossary";

const props = defineProps<{ label: string; type?: SbmlType; field?: string }>();

const summary = computed(() =>
  props.type && props.field ? attributeEntry(props.type, props.field)?.summary : undefined,
);
/** The label of the row is truncated in its 10rem column, so the tooltip repeats it in full
 * before the explanation, the way the native `title` of the label did. */
const tooltip = computed(() => (summary.value ? `${props.label}: ${summary.value}` : props.label));
</script>

<template>
  <div
    class="grid grid-cols-[10rem_minmax(0,1fr)] gap-x-3 border-b border-gray-100 py-1 text-sm"
    data-testid="attribute-row"
  >
    <dt v-tooltip.bottom="tooltip" class="truncate text-gray-500">{{ label }}</dt>
    <dd class="min-w-0 break-words"><slot /></dd>
  </div>
</template>
