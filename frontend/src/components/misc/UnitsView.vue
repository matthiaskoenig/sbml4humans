<script setup lang="ts">
import katex from "katex";
import { computed } from "vue";

import { hasUnitsLatex } from "@/report/units";

const props = defineProps<{ latex: string | null | undefined; units?: string | null }>();

/** "-" is the report's latex of a dimensionless or missing unit: render the placeholder
 * of an empty cell instead of a KaTeX minus. */
const empty = computed(() => !hasUnitsLatex(props.latex));

/** KaTeX has no metrics for the micro sign of the report and warns about it. */
const normalized = computed(() => props.latex?.replaceAll("\u00b5", "\\mu "));

const html = computed(() =>
  !empty.value && normalized.value
    ? katex.renderToString(normalized.value, {
        throwOnError: false,
        strict: "ignore",
        output: "html",
      })
    : "",
);
</script>

<template>
  <span v-if="empty" class="text-gray-400">{{ units || "-" }}</span>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span v-else v-tooltip.bottom="units ?? undefined" data-testid="units" v-html="html" />
</template>
