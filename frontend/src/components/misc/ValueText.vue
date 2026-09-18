<script setup lang="ts">
import { computed } from "vue";

import { formatNumber, numberTooltip, toNumber } from "@/report/number";

const props = defineProps<{ value: string | number | null | undefined; mono?: boolean }>();

/** The double the value stands for, `null` where it is text or nothing at all. An infinite
 * value and a NaN reach the frontend as the constants JSON has no literal for. */
const numeric = computed(() => toNumber(props.value));

const text = computed(() => {
  const { value } = props;
  if (value === null || value === undefined || value === "") return null;
  return numeric.value === null ? String(value) : formatNumber(numeric.value);
});

/** The tooltip of a number: the value without the rounding of the report, or, for an infinite
 * value, what the file writes in its place. */
const full = computed(() => {
  if (numeric.value === null) return undefined;
  const written = numberTooltip(numeric.value);
  if (written !== undefined) return written;
  return text.value !== String(props.value) ? String(props.value) : undefined;
});
</script>

<template>
  <span v-if="text === null" class="text-gray-400">-</span>
  <span v-else v-tooltip.bottom.mono="full" :class="{ 'font-mono': mono || numeric !== null }">{{
    text
  }}</span>
</template>
