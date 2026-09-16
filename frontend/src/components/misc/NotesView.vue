<script setup lang="ts">
import DOMPurify from "dompurify";
import { computed } from "vue";

const props = defineProps<{ notes: string | null | undefined }>();
const html = computed(() =>
  props.notes ? DOMPurify.sanitize(props.notes, { USE_PROFILES: { html: true } }) : "",
);
</script>

<template>
  <p v-if="!html" class="text-gray-400">-</p>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-else class="notes-html" data-testid="notes" v-html="html" />
</template>
