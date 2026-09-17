<script setup lang="ts">
import { computed } from "vue";

import { sanitizeNotes } from "@/report/notes";

const props = defineProps<{ notes: string | null | undefined }>();
const html = computed(() => (props.notes ? sanitizeNotes(props.notes) : ""));
</script>

<template>
  <p v-if="!html" class="text-gray-400">-</p>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-else class="notes-html" data-testid="notes" v-html="html" />
</template>
