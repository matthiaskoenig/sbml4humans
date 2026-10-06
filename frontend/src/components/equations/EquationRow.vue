<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import type { OdeEquation } from "@/api/types";
import { renderLatex } from "@/report/latex";

/** An equation of the differential equations: its left hand side, `=` and its right hand side,
 * the lines of a long sum one below the other. The symbols are the links of KaTeX the backend
 * writes, which the view selects by their `data-pk`.
 *
 * A model with thousands of reactions has thousands of rows, and KaTeX renders one in about a
 * millisecond: a row renders when it comes near the visible part of its scroll, before that it
 * shows its LaTeX as quiet text of about its height. A row whose LaTeX is longer than
 * `MAX_LATEX_LENGTH` stays text until "render formula" renders it. */
const props = defineProps<{ equation: OdeEquation; selected?: boolean; showOrigin?: boolean }>();

const root = ref<HTMLElement | null>(null);
const near = ref(typeof IntersectionObserver === "undefined");
const unlimited = ref(false);
let observer: IntersectionObserver | null = null;

onMounted(() => {
  if (near.value || !root.value) return;
  observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        near.value = true;
        observer?.disconnect();
        observer = null;
      }
    },
    { rootMargin: "600px 0px" },
  );
  observer.observe(root.value);
});
onBeforeUnmount(() => observer?.disconnect());

/** The right hand side: one line, or the lines aligned at their start, a line after the first
 * indented and beginning with its sign. */
const rhs = computed(() => {
  const lines = props.equation.lines;
  if (lines.length <= 1) return lines[0] ?? "";
  return `\\begin{aligned}[t] &${lines.join(" \\\\ &\\quad ")}\\end{aligned}`;
});

const lhsHtml = computed(() =>
  near.value
    ? renderLatex(`\\displaystyle ${props.equation.lhs} =`, {
        links: true,
        unlimited: unlimited.value,
      })
    : null,
);
const rhsHtml = computed(() =>
  near.value
    ? renderLatex(`\\displaystyle ${rhs.value}`, { links: true, unlimited: unlimited.value })
    : null,
);
const rendered = computed(() => lhsHtml.value !== null && rhsHtml.value !== null);

/** The origin of the equation in words, `assignment rule` for `assignment_rule`, shown where the
 * equations of a section have more than one origin: where all have the same it says nothing. */
const origin = computed(() => props.equation.origin.replaceAll("_", " "));
</script>

<template>
  <div
    ref="root"
    class="grid grid-cols-[minmax(0,max-content)_minmax(0,1fr)_auto] items-center gap-x-2 px-4"
    :class="selected ? 'bg-selected' : 'hover:bg-gray-50'"
    :data-equation-of="equation.variable ?? undefined"
    data-testid="equation-row"
  >
    <template v-if="rendered">
      <!-- eslint-disable-next-line vue/no-v-html -->
      <span class="text-right" data-testid="equation-lhs" v-html="lhsHtml" />
      <!-- a scroll box clips both axes: its padding holds the fractions of KaTeX, which reach
      beyond the line box -->
      <!-- eslint-disable-next-line vue/no-v-html -->
      <span class="min-w-0 overflow-x-auto py-1.5" data-testid="equation-rhs" v-html="rhsHtml" />
    </template>
    <template v-else>
      <span class="truncate text-right font-mono text-xs text-gray-400">{{ equation.lhs }} =</span>
      <span class="flex min-w-0 flex-col items-start gap-1">
        <span class="w-full truncate font-mono text-xs text-gray-400">{{ rhs }}</span>
        <button
          v-if="near && !unlimited"
          type="button"
          class="text-xs text-link hover:underline"
          data-testid="equation-render"
          @click.stop="unlimited = true"
        >
          render formula
        </button>
      </span>
    </template>
    <span
      v-if="showOrigin"
      class="rounded bg-gray-100 px-1.5 text-xs whitespace-nowrap text-gray-600"
      data-testid="equation-origin"
      >{{ origin }}</span
    >
  </div>
</template>
