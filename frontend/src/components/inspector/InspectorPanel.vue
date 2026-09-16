<script setup lang="ts">
import { computed, ref, watch } from "vue";

import AnnotationsColumn from "@/components/inspector/AnnotationsColumn.vue";
import AttributesColumn from "@/components/inspector/AttributesColumn.vue";
import LinksColumn from "@/components/inspector/LinksColumn.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import XmlView from "@/components/misc/XmlView.vue";
import { typeInfo } from "@/data/sbmlTypes";
import { useReportIndex } from "@/report/context";
import { useReportView } from "@/report/view";

const props = defineProps<{ pk: string }>();
const index = useReportIndex();
const view = useReportView();

const element = computed(() => index.value?.get(props.pk) ?? null);
const label = computed(() =>
  element.value?.sbmlType ? typeInfo(element.value.sbmlType).label : "",
);
const showXml = ref(false);
watch(
  () => props.pk,
  () => (showXml.value = false),
);
</script>

<template>
  <aside
    v-if="element"
    class="flex h-full flex-col border-t border-gray-200 bg-white"
    data-testid="inspector"
  >
    <header class="flex h-10 shrink-0 items-center gap-2 border-b border-gray-200 px-3 text-sm">
      <TypeMark v-if="element.sbmlType" :type="element.sbmlType" size="md" />
      <span class="text-gray-500" data-testid="inspector-type" :title="element.sbmlType">{{
        label
      }}</span>
      <span class="font-mono font-semibold" data-testid="inspector-id">{{
        element.id ?? element.metaId ?? element.pk
      }}</span>
      <span v-if="element.name" class="truncate text-gray-700" data-testid="inspector-name">{{
        element.name
      }}</span>
      <span class="flex-1" />
      <button
        type="button"
        class="rounded px-2 py-0.5 text-xs"
        :class="
          showXml
            ? 'bg-gray-900 text-white'
            : 'border border-gray-300 text-gray-700 hover:bg-gray-100'
        "
        data-testid="inspector-xml-toggle"
        @click="showXml = !showXml"
      >
        XML
      </button>
      <button
        type="button"
        class="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-900"
        aria-label="close"
        data-testid="inspector-close"
        @click="view.select(null)"
      >
        <i class="pi pi-times text-xs" />
      </button>
    </header>
    <div v-if="showXml" class="min-h-0 flex-1 overflow-hidden p-3">
      <XmlView :xml="element.xml" />
    </div>
    <div v-else class="grid min-h-0 flex-1 grid-cols-3 divide-x divide-gray-200">
      <div class="overflow-y-auto p-3"><AttributesColumn :element="element" /></div>
      <div class="overflow-y-auto p-3"><LinksColumn :pk="element.pk" /></div>
      <div class="overflow-y-auto p-3"><AnnotationsColumn :element="element" /></div>
    </div>
  </aside>
</template>
