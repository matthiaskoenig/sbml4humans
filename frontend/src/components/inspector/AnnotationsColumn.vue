<script setup lang="ts">
import type { SBase } from "@/api/types";
import CvTermList from "@/components/misc/CvTermList.vue";
import HistoryView from "@/components/misc/HistoryView.vue";
import NotesView from "@/components/misc/NotesView.vue";

defineProps<{ element: SBase }>();
</script>

<template>
  <div class="flex flex-col gap-4 text-sm" data-testid="annotations-column">
    <section>
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Annotations</h3>
      <CvTermList :cvterms="element.cvterms ?? []" />
    </section>
    <section>
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Notes</h3>
      <NotesView :notes="element.notes" />
    </section>
    <section v-if="element.history">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">History</h3>
      <HistoryView :history="element.history" />
    </section>
  </div>
</template>
