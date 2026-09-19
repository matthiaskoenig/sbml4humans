<script setup lang="ts">
import { computed } from "vue";

import { formatNumber, numberTooltip, toNumber } from "@/report/number";

const props = defineProps<{
  value: string | number | null | undefined;
  mono?: boolean;
  /** The value is a double of the report, whose infinite values and value which is not a number
   * arrive as the strings `Infinity`, `-Infinity` and `NaN`. A text which reads like one of them,
   * a name or the value of a key value pair, stays the text it is. */
  double?: boolean;
}>();

/** The double the value stands for, `null` where it is text or nothing at all. An infinite
 * value and a NaN reach the frontend as the constants JSON has no literal for, which only a
 * double reads as a number. */
const numeric = computed(() =>
  typeof props.value === "number" || props.double ? toNumber(props.value) : null,
);

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
