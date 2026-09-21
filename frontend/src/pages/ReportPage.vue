<script setup lang="ts">
import { computed, onUnmounted, provide, watch } from "vue";
import { useRoute } from "vue-router";

import { pingLocal } from "@/api/client";
import type { ElementType } from "@/api/types";
import HelpDialog from "@/components/help/HelpDialog.vue";
import InspectorPanel from "@/components/inspector/InspectorPanel.vue";
import AppBar from "@/components/layout/AppBar.vue";
import AppFooter from "@/components/layout/AppFooter.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import SplitPane from "@/components/layout/SplitPane.vue";
import ContextBar from "@/components/report/ContextBar.vue";
import ReportTables from "@/components/report/ReportTables.vue";
import SearchBox from "@/components/report/SearchBox.vue";
import TypeBar, { type TypeCount } from "@/components/report/TypeBar.vue";
import { ELEMENT_TYPES } from "@/data/sbmlTypes";
import { useNarrow } from "@/narrow";
import { ReportIndexKey } from "@/report/context";
import { matches } from "@/report/search";
import { useReportView } from "@/report/view";
import { LOCAL_PING_INTERVAL, useReportStore } from "@/stores/report";

const route = useRoute();
const store = useReportStore();
const view = useReportView();
const narrow = useNarrow();

/** The width the inspector opens with: a third of the window, which leaves the tables the two
 * thirds they need for their widest columns. A reader who drags the divider keeps their width,
 * the split pane remembers it. */
const INSPECTOR_WIDTH = Math.round(window.innerWidth / 3);

/** The narrowest the inspector gets: the labels of the attributes take up to half of it, and
 * below this neither the longest of them nor the value next to it has room left. */
const INSPECTOR_MIN = 360;

watch(
  () => [route.name, route.params.id, route.query.url, route.query.local] as const,
  ([name, id, url, local]) => {
    if (name === "example" && typeof id === "string") void store.loadExample(id);
    else if (name !== "report") return;
    else if (typeof local === "string" && local) void store.loadLocal(local);
    else if (typeof url === "string" && url) void store.loadUrl(url);
  },
  { immediate: true },
);

/** The local server of `sbml4humans.show` ends itself when nobody asks it anything, and a report
 * which is read asks nothing for a long time, so an open local report says that it is still
 * open. A ping which fails says that the server is gone, which the next request will say too. */
let ping: ReturnType<typeof setInterval> | null = null;
watch(
  () => store.source?.kind === "local" && store.response !== null,
  (local) => {
    if (ping !== null) clearInterval(ping);
    ping = local
      ? setInterval(() => void pingLocal().catch(() => undefined), LOCAL_PING_INTERVAL)
      : null;
  },
  { immediate: true },
);
onUnmounted(() => {
  if (ping !== null) clearInterval(ping);
});

/** `/report` holds the report of an upload or of pasted content, which only lives in the store:
 * after a reload, or when the route is entered with the report of an example still loaded, the
 * page shows the empty state instead of a report that does not belong to the route. */
const showsReport = computed(() => {
  // an empty `url=` or `local=` loads nothing, the watcher above skips it too
  const named = [route.query.url, route.query.local].some(
    (value) => typeof value === "string" && value !== "",
  );
  if (route.name !== "report" || named) return true;
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
    const rows = q.trim() ? all.filter((element) => matches(element, q, current)) : all;
    return {
      type: info.type,
      rows,
      all,
      total: all.length,
      list: current.list(currentModel.pk, info.listKey)?.pk ?? null,
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

/** A report opens with its model in the inspector, and so does the model a reader switches to:
 * the model says what the report is about, its name, its notes, its units and its annotations,
 * and a page which opens with the tables alone does not show that there is an inspector. The
 * route is replaced, so that the way back does not pass a report without a selection, and only a
 * model which comes into view selects itself: a reader who closes the inspector keeps it closed,
 * and a url which names an element keeps that element. A narrow window shows the inspector in
 * place of the tables, so its report opens with the tables and without a selection: the model is
 * one tap away in the type bar. */
const defaultPk = computed(() =>
  showsReport.value && !narrow.value && !store.loading && !store.error
    ? (model.value?.pk ?? null)
    : null,
);
watch(
  defaultPk,
  (pk) => {
    if (pk && !view.state.value.pk) void view.select(pk, "replace");
  },
  { immediate: true },
);
watch([selectedPk, index], ([pk, current]) => {
  if (pk && current && !current.has(pk)) {
    console.warn(`The selected element ${pk} is not part of the report`);
    void view.select(null, "replace");
  }
});
</script>

<template>
  <AppBar>
    <template #search>
      <SearchBox v-if="index" />
    </template>
    <template #context>
      <ContextBar
        v-if="index && model && entry"
        :index="index"
        :entries="store.entries"
        :entry="entry"
        :model="model"
      />
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
  <div v-else-if="index && model" class="flex min-h-0 flex-1 flex-col" data-testid="report-page">
    <!-- the bar is about the tables, and on a narrow window the inspector stands in their place:
    it gives its rows to the element which is read -->
    <TypeBar v-show="!(narrow && selectedPk)" :index="index" :model="model" :counts="counts" />
    <!-- the inspector is the first pane: the element which is read stands at the left, where a
    reader begins, and the tables it was selected in keep the rest of the window -->
    <SplitPane
      v-if="!narrow"
      direction="horizontal"
      storage-key="inspector-width"
      :initial="INSPECTOR_WIDTH"
      :min="INSPECTOR_MIN"
      sized-pane="first"
      :collapsed="!selectedPk"
    >
      <template #first>
        <InspectorPanel v-if="selectedPk" :pk="selectedPk" />
      </template>
      <template #second>
        <ReportTables :sections="visibleSections" :empty-message="emptyMessage" />
      </template>
    </SplitPane>
    <!-- a narrow window has no room for the two next to each other: the tables are the page, and
    the element a reader selects takes their place until the reader returns. The tables stay
    mounted below it, so that they are where the reader left them -->
    <div v-else class="flex min-h-0 flex-1 flex-col" data-testid="report-stack">
      <InspectorPanel v-if="selectedPk" :pk="selectedPk" class="min-h-0 flex-1" />
      <ReportTables
        v-show="!selectedPk"
        class="min-h-0 flex-1"
        :sections="visibleSections"
        :empty-message="emptyMessage"
      />
    </div>
    <!-- a narrow window leaves the footer to the home page and the examples page, the height it
    takes is the height the report is read in -->
    <AppFooter dense class="max-md:hidden" />
    <!-- the explanation of the entry the route names, mounted once for the whole page: every
    label which opens one opens it here -->
    <HelpDialog />
  </div>
</template>
