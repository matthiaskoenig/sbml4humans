<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { typeInfo } from "@/data/sbmlTypes";
import { typeEntry } from "@/report/glossary";

const props = withDefaults(defineProps<{ type: SbmlType; size?: "sm" | "md" }>(), { size: "sm" });
const info = computed(() => typeInfo(props.type));
/** The icon is the only sign of the type in an element link and in the type bar, so the tooltip
 * names the type before it explains it, and the label is the accessible name of the mark. */
const summary = computed(() => typeEntry(props.type)?.summary);
const tooltip = computed(() =>
  summary.value ? `${info.value.label}: ${summary.value}` : info.value.label,
);
</script>

<template>
  <span
    v-tooltip.bottom="tooltip"
    class="inline-flex shrink-0 items-center justify-center rounded-sm text-gray-800"
    :class="size === 'sm' ? 'size-4' : 'size-6'"
    :style="{ backgroundColor: info.color }"
    role="img"
    :aria-label="info.label"
    data-testid="type-mark"
  >
    <component :is="info.icon" :class="size === 'sm' ? 'size-2.5' : 'size-3.5'" />
  </span>
</template>
