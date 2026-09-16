<script setup lang="ts">
import katex from "katex";
import { computed } from "vue";

import type { Math } from "@/api/types";

const props = defineProps<{ math: Math | null | undefined; display?: boolean }>();

const html = computed(() =>
  props.math
    ? katex.renderToString(props.math.latex, {
        throwOnError: false,
        displayMode: props.display ?? false,
        output: "html",
      })
    : "",
);

function copy(event: MouseEvent): void {
  if (!props.math) return;
  event.stopPropagation();
  void navigator.clipboard?.writeText(props.math.formula);
}
</script>

<template>
  <span v-if="!math" class="text-gray-400">-</span>
  <span
    v-else
    v-tooltip.bottom="`${math.formula} (click to copy)`"
    class="cursor-copy"
    :class="{ 'block overflow-x-auto': display }"
    data-testid="math"
    @click="copy"
  >
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span v-html="html" />
  </span>
</template>
