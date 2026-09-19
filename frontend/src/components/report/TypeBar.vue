<script setup lang="ts">
import { computed } from "vue";

import type { ElementType, Model } from "@/api/types";
import TypeMark from "@/components/misc/TypeMark.vue";
import { ELEMENT_TYPES, type ElementTypeInfo } from "@/data/sbmlTypes";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";

export interface TypeCount {
  total: number;
  matched: number;
}

const props = defineProps<{
  index: ReportIndex;
  model: Model;
  counts: Map<ElementType, TypeCount>;
}>();
const view = useReportView();

const packages = computed(
  () => new Set(props.index.document.packages?.map((pkg) => pkg.prefix) ?? []),
);

/** The types the model has elements of, in the order of the specification with the unit
 * definitions last, which is the order of `ELEMENT_TYPES`: a type of a package
 * the document does not declare, and a type the model states no element of, is not an entry of
 * the bar at all. The count of a type is its number of elements, which a search does not change,
 * so the entries of the bar stay the same while a search runs. */
const types = computed<ElementTypeInfo[]>(() =>
  ELEMENT_TYPES.filter(
    (info) =>
      (info.pkg === "core" || packages.value.has(info.pkg)) &&
      (props.counts.get(info.type)?.total ?? 0) > 0,
  ),
);

const visible = computed(() => view.state.value.types);
const searching = computed(() => view.state.value.q.trim() !== "");

function isVisible(type: ElementType): boolean {
  return visible.value === null || visible.value.includes(type);
}

function toggle(type: ElementType): void {
  const all = types.value.map((info) => info.type);
  // a `types=` of an older url can name a type this model has no element of, dropping those
  // keeps the toggle a filter over the types of the bar instead of clearing the filter entirely
  const current = visible.value?.filter((t) => all.includes(t)) ?? all;
  const next = current.includes(type)
    ? current.filter((t) => t !== type)
    : all.filter((t) => t === type || current.includes(t));
  void view.setTypes(next.length === all.length ? null : next);
}

function scrollTo(type: ElementType): void {
  document
    .getElementById(`section-${type}`)
    ?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function selectedClass(pk: string): string {
  return view.state.value.pk === pk ? "bg-selected" : "hover:bg-gray-100";
}
</script>

<template>
  <!-- one row of entries which wraps onto as many lines as the model needs: the document and the
  model of the report first, then the types the model uses -->
  <nav
    class="flex shrink-0 flex-wrap items-center gap-x-5 gap-y-1 border-b border-gray-200 px-4 py-1.5 text-sm"
    data-testid="type-bar"
  >
    <button
      type="button"
      class="flex items-center gap-1.5 rounded px-1 py-0.5"
      :class="selectedClass(index.document.pk)"
      data-testid="bar-document"
      @click="view.select(index.document.pk)"
    >
      <TypeMark type="SBMLDocument" />SBMLDocument
    </button>
    <button
      type="button"
      class="flex items-center gap-1.5 rounded px-1 py-0.5"
      :class="selectedClass(model.pk)"
      data-testid="bar-model"
      @click="view.select(model.pk)"
    >
      <TypeMark type="Model" /><span class="font-mono">{{ model.id }}</span>
    </button>
    <button
      v-for="emd in index.externalModelDefinitions"
      :key="emd.pk"
      type="button"
      class="flex items-center gap-1.5 rounded px-1 py-0.5"
      :class="selectedClass(emd.pk)"
      data-testid="bar-emd"
      @click="view.select(emd.pk)"
    >
      <TypeMark type="ExternalModelDefinition" /><span class="font-mono">{{ emd.id }}</span>
    </button>

    <!-- the quiet separator between the document and what the model is made of, which a model
    without a single element does not need -->
    <span v-if="types.length > 0" class="h-4 w-px bg-gray-300" aria-hidden="true" />

    <span
      v-for="info in types"
      :key="info.type"
      class="flex items-center gap-1.5 text-gray-800"
      :data-testid="`bar-type-${info.type}`"
    >
      <input
        type="checkbox"
        class="size-3.5 accent-gray-700"
        :checked="isVisible(info.type)"
        :aria-label="`show ${info.plural}`"
        :data-testid="`bar-toggle-${info.type}`"
        @change="toggle(info.type)"
      />
      <button
        type="button"
        class="flex items-center gap-1.5 hover:underline"
        @click="scrollTo(info.type)"
      >
        <TypeMark :type="info.type" />{{ info.plural }}
      </button>
      <span
        class="font-mono text-xs text-gray-500 tabular-nums"
        :data-testid="`bar-count-${info.type}`"
      >
        <template v-if="searching">{{ counts.get(info.type)?.matched ?? 0 }} / </template
        >{{ counts.get(info.type)?.total ?? 0 }}
      </span>
    </span>
  </nav>
</template>
