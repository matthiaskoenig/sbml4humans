<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ value: string | number | null | undefined; mono?: boolean }>();

const text = computed(() => {
  const { value } = props;
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : String(Number(value.toPrecision(6)));
  }
  return value;
});

const full = computed(() =>
  typeof props.value === "number" && text.value !== String(props.value)
    ? String(props.value)
    : undefined,
);
</script>

<template>
  <span v-if="text === null" class="text-gray-400">-</span>
  <span
    v-else
    v-tooltip.bottom="full"
    :class="{ 'font-mono': mono || typeof value === 'number' }"
    >{{ text }}</span
  >
</template>
