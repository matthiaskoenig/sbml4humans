<script setup lang="ts">
import { computed, provide, watch } from "vue";
import { useRoute } from "vue-router";

import type { SbmlElement, ElementType } from "@/api/types";
import InspectorPanel from "@/components/inspector/InspectorPanel.vue";
import AppBar from "@/components/layout/AppBar.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import SplitPane from "@/components/layout/SplitPane.vue";
import ContextBar from "@/components/report/ContextBar.vue";
import ElementSection from "@/components/report/ElementSection.vue";
import SearchBox from "@/components/report/SearchBox.vue";
import TypeRail, { type TypeCount } from "@/components/report/TypeRail.vue";
import { ELEMENT_TYPES } from "@/data/sbmlTypes";
import { ReportIndexKey } from "@/report/context";
import { matches } from "@/report/search";
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

/** `/report` holds the report of an upload or of pasted content, which only lives in the store:
 * after a reload, or when the route is entered with the report of an example still loaded, the
 * page shows the empty state instead of a report that does not belong to the route. */
const showsReport = computed(() => {
  if (route.name !== "report" || typeof route.query.url === "string") return true;
  const kind = store.source?.kind;
  return kind === "file" || kind === "content";
});

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

/** The elements of the current model per type, filtered by the search. */
const sections = computed(() => {
  const current = index.value;
  const currentModel = model.value;
  if (!current || !currentModel?.id) return [];
  const byType = current.byType(currentModel.id);
  const { q, types } = view.state.value;
  return ELEMENT_TYPES.map((info) => {
    const all = byType.get(info.type) ?? [];
    const rows = q.trim() ? all.filter((element) => matches(element, q)) : all;
    return {
      type: info.type,
      rows,
      total: all.length,
      visible: types === null || types.includes(info.type),
    };
  });
});

const counts = computed(
  () =>
    new Map<ElementType, TypeCount>(
      sections.value.map((s) => [s.type, { total: s.total, matched: s.rows.length }]),
    ),
);
const visibleSections = computed(() =>
  sections.value.filter((s) => s.visible && s.rows.length > 0),
);
/** A model without any element is empty, it does not hide its elements behind the filters. */
const emptyMessage = computed(() =>
  sections.value.every((s) => s.total === 0) ? "This model has no elements." : "No elements match.",
);

const selectedPk = computed(() => view.state.value.pk);
watch([selectedPk, index], ([pk, current]) => {
  if (pk && current && !current.has(pk)) {
    console.warn(`The selected element ${pk} is not part of the report`);
    void view.select(null, "replace");
  }
});
</script>

<template>
  <AppBar>
    <template #context>
      <ContextBar
        v-if="index && model && entry"
        :index="index"
        :entries="store.entries"
        :entry="entry"
        :model="model"
      />
    </template>
    <template #actions>
      <SearchBox v-if="index" />
    </template>
  </AppBar>
  <LoadingState v-if="store.loading" :message="`Loading ${store.source?.name ?? 'report'}`" />
  <ErrorState v-else-if="store.error" :error="store.error" />
  <div
    v-else-if="!store.response || !showsReport"
    class="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-gray-600"
    data-testid="no-report"
  >
    <p>No report loaded.</p>
    <RouterLink to="/" class="text-link hover:underline">Load a model</RouterLink>
  </div>
  <SplitPane
    v-else-if="index && model"
    direction="horizontal"
    storage-key="rail"
    :initial="240"
    :min="160"
    data-testid="report-page"
  >
    <template #first>
      <TypeRail :index="index" :model="model" :counts="counts" />
    </template>
    <template #second>
      <SplitPane
        direction="vertical"
        storage-key="inspector"
        :initial="320"
        :min="160"
        sized-pane="second"
        :collapsed="!selectedPk"
      >
        <template #first>
          <div class="h-full overflow-y-auto px-4 pb-8" data-testid="tables">
            <p
              v-if="visibleSections.length === 0"
              class="p-8 text-center text-sm text-gray-500"
              data-testid="no-matches"
            >
              {{ emptyMessage }}
            </p>
            <ElementSection
              v-for="section in visibleSections"
              :key="section.type"
              :type="section.type"
              :rows="section.rows as SbmlElement[]"
              :total="section.total"
            />
          </div>
        </template>
        <template #second>
          <InspectorPanel v-if="selectedPk" :pk="selectedPk" />
        </template>
      </SplitPane>
    </template>
  </SplitPane>
</template>
