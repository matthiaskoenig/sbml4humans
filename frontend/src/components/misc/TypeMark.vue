<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { typeInfo } from "@/data/sbmlTypes";
import { typeEntry } from "@/report/glossary";

const props = withDefaults(defineProps<{ type: SbmlType; size?: "sm" | "md" }>(), { size: "sm" });
const info = computed(() => typeInfo(props.type));
const summary = computed(() => typeEntry(props.type)?.summary);
</script>

<template>
  <span
    v-tooltip.bottom="summary"
    class="inline-flex shrink-0 items-center justify-center rounded-sm text-gray-800"
    :class="size === 'sm' ? 'size-4' : 'size-6'"
    :style="{ backgroundColor: info.color }"
    data-testid="type-mark"
  >
    <component :is="info.icon" :class="size === 'sm' ? 'size-2.5' : 'size-3.5'" />
  </span>
</template>
