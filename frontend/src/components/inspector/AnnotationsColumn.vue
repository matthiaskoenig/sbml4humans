<script setup lang="ts">
import { computed } from "vue";

import type { SBase } from "@/api/types";
import CvTermList from "@/components/misc/CvTermList.vue";
import HistoryView from "@/components/misc/HistoryView.vue";
import XhtmlView from "@/components/misc/XhtmlView.vue";
import { hasNotes } from "@/report/notes";

const props = defineProps<{ element: SBase }>();
const showsNotes = computed(() => hasNotes(props.element.notes));
</script>

<template>
  <div class="flex flex-col gap-4 text-sm" data-testid="annotations-column">
    <section>
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Annotations</h3>
      <CvTermList :cvterms="element.cvterms ?? []" />
    </section>
    <!-- most elements of most models carry no notes, and a heading over a dash on every one of
    them is a line a reader learns to skip; the annotations keep theirs, the section is named
    after them -->
    <section v-if="showsNotes" data-testid="notes-section">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Notes</h3>
      <XhtmlView :xhtml="element.notes" testid="notes" />
    </section>
    <section v-if="element.history">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">History</h3>
      <HistoryView :history="element.history" />
    </section>
  </div>
</template>
