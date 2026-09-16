<script setup lang="ts">
import katex from "katex";
import { computed } from "vue";

const props = defineProps<{ latex: string | null | undefined; units?: string | null }>();

/** KaTeX has no metrics for the micro sign of the report and warns about it. */
const normalized = computed(() => props.latex?.replaceAll("\u00b5", "\\mu "));

const html = computed(() =>
  normalized.value
    ? katex.renderToString(normalized.value, {
        throwOnError: false,
        strict: "ignore",
        output: "html",
      })
    : "",
);
</script>

<template>
  <span v-if="!latex" class="text-gray-400">{{ units || "-" }}</span>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span v-else v-tooltip.bottom="units ?? undefined" data-testid="units" v-html="html" />
</template>
