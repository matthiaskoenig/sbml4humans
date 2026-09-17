<script setup lang="ts">
import { computed } from "vue";

import type { SbmlType } from "@/api/types";
import { typeInfo } from "@/data/sbmlTypes";

const props = withDefaults(defineProps<{ type: SbmlType; size?: "sm" | "md" }>(), { size: "sm" });
const info = computed(() => typeInfo(props.type));
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-sm text-gray-800"
    :class="size === 'sm' ? 'size-4' : 'size-6'"
    :style="{ backgroundColor: info.color }"
    :title="info.label"
    data-testid="type-mark"
  >
    <component :is="info.icon" :class="size === 'sm' ? 'size-2.5' : 'size-3.5'" />
  </span>
</template>
