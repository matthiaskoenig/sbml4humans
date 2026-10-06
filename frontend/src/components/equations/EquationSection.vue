<script setup lang="ts">
import { computed } from "vue";

import HelpButton from "@/components/help/HelpButton.vue";
import { conceptEntry, conceptKey } from "@/report/glossary";

/** A section of the differential equations: its heading with the help of its entry of the
 * glossary and the number of its equations, the summary of the entry, and its rows. */
const props = defineProps<{ concept: string; count: number }>();

const entry = computed(() => conceptEntry(props.concept));
const helpKey = computed(() => conceptKey(props.concept));
</script>

<template>
  <section class="border-b border-gray-100 pb-2" :data-testid="`equations-${concept}`">
    <h3
      class="sticky top-0 z-10 flex items-baseline gap-2 bg-white px-4 pt-3 pb-1 text-sm font-semibold"
    >
      <span class="first-letter:uppercase">{{ entry?.label ?? concept }}</span>
      <HelpButton v-if="helpKey" :help-key="helpKey" :label="entry?.label ?? concept" />
      <span class="font-mono text-xs font-normal text-gray-500" data-testid="equations-count">{{
        count
      }}</span>
    </h3>
    <p v-if="entry?.summary" class="px-4 pb-1 text-xs text-gray-500 first-letter:uppercase">
      {{ entry.summary }}
    </p>
    <slot />
  </section>
</template>
