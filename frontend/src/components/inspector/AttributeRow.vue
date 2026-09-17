<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { attributeEntry } from "@/report/glossary";

const props = defineProps<{ label: string; type?: SbmlType; field?: string }>();

const summary = computed(() =>
  props.type && props.field ? attributeEntry(props.type, props.field)?.summary : undefined,
);
</script>

<template>
  <div
    class="grid grid-cols-[10rem_minmax(0,1fr)] gap-x-3 border-b border-gray-100 py-1 text-sm"
    data-testid="attribute-row"
  >
    <dt v-tooltip.bottom="summary" class="truncate text-gray-500">{{ label }}</dt>
    <dd class="min-w-0 break-words"><slot /></dd>
  </div>
</template>
