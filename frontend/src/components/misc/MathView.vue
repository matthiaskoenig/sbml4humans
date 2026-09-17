<script setup lang="ts">
import { computed, ref } from "vue";

import type { Math } from "@/api/types";
import { renderLatex } from "@/report/latex";

const props = defineProps<{ math: Math | null | undefined; display?: boolean }>();

/** Set once the "render formula" button of the display mode is clicked, for this instance only. */
const forceUnlimited = ref(false);

/** Null when the formula is too long to render by default and has not been forced yet, or when
 * KaTeX throws. */
const html = computed(() =>
  props.math
    ? renderLatex(props.math.latex, {
        display: props.display ?? false,
        unlimited: forceUnlimited.value,
      })
    : null,
);

const truncatedFormula = computed(() => {
  const formula = props.math?.formula ?? "";
  return formula.length > 120 ? `${formula.slice(0, 120)}…` : formula;
});

function copy(event: MouseEvent): void {
  if (!props.math) return;
  event.stopPropagation();
  // a formula can contain line breaks the tooltip does not show, so every run of whitespace
  // collapses to a single space before it is copied.
  void navigator.clipboard?.writeText(props.math.formula.replace(/\s+/g, " "));
}
</script>

<template>
  <span v-if="!math" class="text-gray-400">-</span>
  <span
    v-else-if="html !== null"
    v-tooltip.bottom="`${math.formula} (click to copy)`"
    class="cursor-copy"
    :class="{ 'block overflow-x-auto': display }"
    data-testid="math"
    @click="copy"
  >
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span v-html="html" />
  </span>
  <span v-else class="flex items-center gap-2">
    <span
      v-tooltip.bottom="`${math.formula} (click to copy)`"
      class="cursor-copy font-mono"
      data-testid="math-text"
      @click="copy"
      >{{ truncatedFormula }}</span
    >
    <button
      v-if="display"
      type="button"
      class="text-xs text-link hover:underline"
      data-testid="math-render"
      @click.stop="forceUnlimited = true"
    >
      render formula
    </button>
  </span>
</template>
