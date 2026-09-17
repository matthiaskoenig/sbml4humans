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

/** Package types only when the document declares the package; empty types last. */
const types = computed<ElementTypeInfo[]>(() => {
  const declared = ELEMENT_TYPES.filter(
    (info) => info.pkg === "core" || packages.value.has(info.pkg),
  );
  const total = (info: ElementTypeInfo) => props.counts.get(info.type)?.total ?? 0;
  return [
    ...declared.filter((info) => total(info) > 0),
    ...declared.filter((info) => total(info) === 0),
  ];
});

const visible = computed(() => view.state.value.types);
const searching = computed(() => view.state.value.q.trim() !== "");

function isVisible(type: ElementType): boolean {
  return visible.value === null || visible.value.includes(type);
}

function toggle(type: ElementType): void {
  const all = types.value.map((info) => info.type);
  // a `types=` of an older url can name a type the document does not declare, dropping those
  // keeps the toggle a filter over the declared types instead of clearing the filter entirely
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
  <nav class="flex h-full flex-col overflow-y-auto py-2 text-sm" data-testid="type-rail">
    <p class="px-3 pb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">Document</p>
    <button
      type="button"
      class="flex items-center gap-2 px-3 py-1 text-left"
      :class="selectedClass(index.document.pk)"
      data-testid="rail-document"
      @click="view.select(index.document.pk)"
    >
      <TypeMark type="SBMLDocument" /><span class="truncate">SBMLDocument</span>
    </button>
    <button
      type="button"
      class="flex items-center gap-2 px-3 py-1 text-left"
      :class="selectedClass(model.pk)"
      data-testid="rail-model"
      @click="view.select(model.pk)"
    >
      <TypeMark type="Model" /><span class="truncate font-mono">{{ model.id }}</span>
    </button>
    <button
      v-for="emd in index.externalModelDefinitions"
      :key="emd.pk"
      type="button"
      class="flex items-center gap-2 px-3 py-1 text-left"
      :class="selectedClass(emd.pk)"
      data-testid="rail-emd"
      @click="view.select(emd.pk)"
    >
      <TypeMark type="ExternalModelDefinition" /><span class="truncate font-mono">{{
        emd.id
      }}</span>
    </button>

    <p class="px-3 pt-4 pb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
      Elements
    </p>
    <div
      v-for="info in types"
      :key="info.type"
      class="flex items-center gap-2 px-3 py-1"
      :class="(counts.get(info.type)?.total ?? 0) === 0 ? 'text-gray-400' : 'text-gray-800'"
      :data-testid="`rail-type-${info.type}`"
    >
      <input
        type="checkbox"
        class="size-3.5 accent-gray-700"
        :checked="isVisible(info.type)"
        :aria-label="`show ${info.plural}`"
        :data-testid="`rail-toggle-${info.type}`"
        @change="toggle(info.type)"
      />
      <TypeMark :type="info.type" />
      <button
        type="button"
        class="flex-1 truncate text-left hover:underline"
        @click="scrollTo(info.type)"
      >
        {{ info.plural }}
      </button>
      <span class="font-mono text-xs tabular-nums" :data-testid="`rail-count-${info.type}`">
        <template v-if="searching">{{ counts.get(info.type)?.matched ?? 0 }} / </template
        >{{ counts.get(info.type)?.total ?? 0 }}
      </span>
    </div>
  </nav>
</template>
