<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";

import { useReportView } from "@/report/view";

const view = useReportView();
const text = ref(view.state.value.q);
let timer: ReturnType<typeof setTimeout> | undefined;

watch(
  () => view.state.value.q,
  (q) => {
    if (q !== text.value) text.value = q;
  },
);

watch(text, (value) => {
  clearTimeout(timer);
  timer = setTimeout(() => void view.setSearch(value), 150);
});

// a pending search must not write the query of this page into the route of the next one
onBeforeUnmount(() => clearTimeout(timer));
</script>

<template>
  <div class="relative">
    <i
      class="pi pi-search pointer-events-none absolute top-1/2 left-2 -translate-y-1/2 text-xs text-gray-400"
    />
    <input
      v-model="text"
      type="search"
      placeholder="Search id, name, notes, math"
      class="w-72 rounded border border-gray-300 py-1 pr-2 pl-7 text-sm focus:border-link focus:outline-none"
      data-testid="search-input"
      @keydown.esc="text = ''"
    />
  </div>
</template>
