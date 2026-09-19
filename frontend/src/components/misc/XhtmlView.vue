<script setup lang="ts">
import { computed } from "vue";

import { sanitizeNotes } from "@/report/notes";

/** The XHTML an element carries, rendered with the markup the report allows: the notes of every
 * element and the message of a constraint, which core §4.10.2 puts under the rules of the notes.
 * `testid` names what is rendered, so a test can tell the two apart. */
const props = withDefaults(defineProps<{ xhtml: string | null | undefined; testid?: string }>(), {
  testid: "xhtml",
});
const html = computed(() => (props.xhtml ? sanitizeNotes(props.xhtml) : ""));
</script>

<template>
  <p v-if="!html" class="text-gray-400">-</p>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-else class="notes-html" :data-testid="testid" v-html="html" />
</template>
