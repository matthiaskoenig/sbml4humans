<script setup lang="ts">
import { ExternalLinkIcon, XIcon } from "@lucide/vue";
import { computed, ref, watch } from "vue";

import AnnotationsColumn from "@/components/inspector/AnnotationsColumn.vue";
import AttributesColumn from "@/components/inspector/AttributesColumn.vue";
import LinksColumn from "@/components/inspector/LinksColumn.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import XmlView from "@/components/misc/XmlView.vue";
import { typeInfo } from "@/data/sbmlTypes";
import { useReportIndex } from "@/report/context";
import { referenceUrl } from "@/report/glossary";
import { elementLabel } from "@/report/label";
import { useReportView } from "@/report/view";

const props = defineProps<{ pk: string }>();
const index = useReportIndex();
const view = useReportView();

const element = computed(() => index.value?.get(props.pk) ?? null);
const label = computed(() =>
  element.value?.sbmlType ? typeInfo(element.value.sbmlType).label : "",
);
/** The element is named as every link to it names it; the type is already named next to it. */
const name = computed(() => elementLabel(index.value, props.pk) ?? "");
const showXml = ref(false);
watch(
  () => props.pk,
  () => (showXml.value = false),
);
/** The document and the model contain the whole file, so the report carries the annotation
 * element of the two in the place of their XML: a tool writes its own vocabulary there, and
 * without it a reader cannot see what a file says about itself. */
const annotationOf = computed(() => {
  const sbase = element.value;
  if (sbase?.sbmlType === "SBMLDocument") return "document";
  if (sbase?.sbmlType === "Model") return "model";
  return null;
});
const xml = computed(() => {
  const sbase = element.value;
  if (!sbase) return null;
  if (sbase.sbmlType === "SBMLDocument" || sbase.sbmlType === "Model") {
    return sbase.annotationXml ?? null;
  }
  return sbase.xml ?? null;
});
const xmlCaption = computed(() =>
  annotationOf.value ? `The annotation element of the ${annotationOf.value}.` : undefined,
);
const xmlEmptyMessage = computed(() =>
  annotationOf.value
    ? `The ${annotationOf.value} carries no annotation, and its XML is the whole file, which is not part of the report.`
    : "No XML available.",
);
</script>

<template>
  <aside v-if="element" class="flex h-full flex-col bg-white" data-testid="inspector">
    <header class="flex h-10 shrink-0 items-center gap-2 border-b border-gray-200 px-3 text-sm">
      <TypeMark v-if="element.sbmlType" :type="element.sbmlType" size="md" />
      <a
        v-if="element.sbmlType"
        :href="referenceUrl(element.sbmlType)"
        target="_blank"
        rel="noopener"
        data-testid="inspector-type-link"
        class="flex items-center gap-1 text-link hover:underline"
      >
        <span data-testid="inspector-type">{{ label }}</span>
        <ExternalLinkIcon class="size-3" />
      </a>
      <span v-else class="text-gray-500" data-testid="inspector-type">{{ label }}</span>
      <span class="font-mono font-semibold" data-testid="inspector-id">{{ name }}</span>
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
        <XIcon class="size-3" />
      </button>
    </header>
    <div v-if="showXml" class="min-h-0 flex-1 overflow-hidden p-3">
      <XmlView :xml="xml" :caption="xmlCaption" :empty-message="xmlEmptyMessage" />
    </div>
    <!-- the inspector is a column of the report page, a third of the window wide, and its three
    sections are one under the other in one scroll; a reader who drags it wider than `@4xl` gets
    the three columns next to each other, each with a scroll of its own -->
    <div v-else class="@container min-h-0 flex-1 overflow-hidden" data-testid="inspector-body">
      <div
        class="grid h-full grid-cols-1 divide-y divide-gray-200 overflow-y-auto @4xl:grid-cols-3 @4xl:divide-x @4xl:divide-y-0 @4xl:overflow-hidden"
      >
        <div class="p-3 @4xl:min-h-0 @4xl:overflow-y-auto">
          <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase @4xl:hidden">
            Attributes
          </h3>
          <AttributesColumn :element="element" />
        </div>
        <div class="p-3 @4xl:min-h-0 @4xl:overflow-y-auto"><LinksColumn :pk="element.pk" /></div>
        <div class="p-3 @4xl:min-h-0 @4xl:overflow-y-auto">
          <AnnotationsColumn :element="element" />
        </div>
      </div>
    </div>
  </aside>
</template>
