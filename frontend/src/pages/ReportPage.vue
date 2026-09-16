<script setup lang="ts">
import { computed, provide, watch } from "vue";
import { useRoute } from "vue-router";

import AppBar from "@/components/layout/AppBar.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import { ReportIndexKey } from "@/report/context";
import { useReportView } from "@/report/view";
import { useReportStore } from "@/stores/report";

const route = useRoute();
const store = useReportStore();
const view = useReportView();

watch(
  () => [route.name, route.params.id, route.query.url] as const,
  ([name, id, url]) => {
    if (name === "example" && typeof id === "string") void store.loadExample(id);
    else if (name === "report" && typeof url === "string" && url) void store.loadUrl(url);
  },
  { immediate: true },
);

/** The entry of the route if it exists, else the default entry. */
const entry = computed(() => {
  const requested = view.state.value.entry;
  return requested && store.entries.includes(requested) ? requested : store.defaultEntry;
});

const index = computed(() => (entry.value ? store.indexFor(entry.value) : null));
provide(ReportIndexKey, index);

/** The model of the route if it exists in the entry, else the main model. */
const model = computed(() => {
  const current = index.value;
  if (!current) return null;
  const requested = view.state.value.model;
  return (requested ? current.model(requested) : null) ?? current.mainModel;
});
</script>

<template>
  <AppBar />
  <LoadingState v-if="store.loading" :message="`Loading ${store.source?.name ?? 'report'}`" />
  <ErrorState v-else-if="store.error" :error="store.error" />
  <div
    v-else-if="!store.response"
    class="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-gray-600"
    data-testid="no-report"
  >
    <p>No report loaded.</p>
    <RouterLink to="/" class="text-link hover:underline">Load a model</RouterLink>
  </div>
  <main v-else class="flex min-h-0 flex-1 flex-col p-4" data-testid="report-page">
    <p class="text-sm text-gray-600">
      {{ store.source?.name }}: entry {{ entry }}, model {{ model?.id }},
      {{ index?.elements.size }} elements
    </p>
  </main>
</template>
