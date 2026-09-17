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
    :class="size === 'sm' ? 'size-4 text-[10px]' : 'size-6 text-sm'"
    :style="{ backgroundColor: info.color }"
    :title="info.label"
    data-testid="type-mark"
  >
    <i class="pi" :class="info.icon" />
  </span>
</template>
