<script setup lang="ts">
import katex from "katex";
import { computed } from "vue";

const props = defineProps<{ latex: string | null | undefined; units?: string | null }>();

const html = computed(() =>
  props.latex ? katex.renderToString(props.latex, { throwOnError: false, output: "html" }) : "",
);
</script>

<template>
  <span v-if="!latex" class="text-gray-400">{{ units || "-" }}</span>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span v-else v-tooltip.bottom="units ?? undefined" data-testid="units" v-html="html" />
</template>
