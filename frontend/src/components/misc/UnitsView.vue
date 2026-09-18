<script setup lang="ts">
import { computed } from "vue";

import { renderLatex } from "@/report/latex";
import { hasUnitsLatex } from "@/report/units";

const props = defineProps<{ latex: string | null | undefined; units?: string | null }>();

/** Null for a dimensionless or missing unit (the report's "-" placeholder) and for a unit whose
 * latex is too long to render or that KaTeX throws on: the placeholder of an empty cell shows in
 * every one of these cases, never a KaTeX minus or a blank cell. */
const html = computed(() => (hasUnitsLatex(props.latex) ? renderLatex(props.latex!) : null));
</script>

<template>
  <span v-if="html === null" class="text-gray-400">{{ units || "-" }}</span>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span v-else v-tooltip.bottom.mono="units ?? undefined" data-testid="units" v-html="html" />
</template>
