<script setup lang="ts">
import { CircleAlertIcon, InfoIcon, TriangleAlertIcon } from "@lucide/vue";
import { computed } from "vue";

import type { Severity } from "@/report/validation";

/** The mark of a severity: red for an error, amber for a warning, gray for a note. Its accessible
 * name is the severity, or `label` where the mark stands for more than its severity. */
const props = withDefaults(
  defineProps<{ severity: Severity; size?: "sm" | "md"; label?: string }>(),
  { size: "sm", label: undefined },
);

const icon = computed(
  () => ({ error: CircleAlertIcon, warning: TriangleAlertIcon, info: InfoIcon })[props.severity],
);
const color = computed(
  () =>
    ({ error: "text-red-600", warning: "text-amber-500", info: "text-gray-400" })[props.severity],
);
</script>

<template>
  <component
    :is="icon"
    :class="[color, size === 'sm' ? 'size-3.5' : 'size-4']"
    class="shrink-0"
    :aria-label="label ?? severity"
    role="img"
    :data-testid="`severity-${severity}`"
  />
</template>
