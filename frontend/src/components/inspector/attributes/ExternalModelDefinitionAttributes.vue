<script setup lang="ts">
import { computed } from "vue";

import type { ExternalModelDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { RESOLUTION_STATUS_LABELS } from "@/data/resolutionStatus";
import { useReportIndex } from "@/report/context";
import { useReportView } from "@/report/view";

const props = defineProps<{ element: ExternalModelDefinition }>();
const index = useReportIndex();
const view = useReportView();

const resolution = computed(() => props.element.resolution);
const status = computed(() => resolution.value?.status ?? "notFound");
/** The entry the source names, which is linked where the report holds a model of it: an entry
 * which is no SBML is named by the archive and has no report to open. */
const entry = computed(() => resolution.value?.entry ?? null);
const entryIndex = computed(() => {
  const other = entry.value ? index.value?.entry(entry.value) : null;
  return other && other !== index.value ? other : null;
});
</script>

<template>
  <AttributeRow label="source" :type="element.sbmlType" field="source"
    ><ValueText :value="element.source" mono
  /></AttributeRow>
  <AttributeRow label="model ref" :type="element.sbmlType" field="modelRef"
    ><ValueText :value="element.modelRef" mono
  /></AttributeRow>
  <AttributeRow label="md5" :type="element.sbmlType" field="md5"
    ><ValueText :value="element.md5" mono
  /></AttributeRow>
  <AttributeRow label="status" :type="element.sbmlType" field="resolution.status">
    <span
      :class="status === 'resolved' ? 'text-gray-900' : 'text-amber-700'"
      :data-status="status"
      data-testid="resolution-status"
      >{{ RESOLUTION_STATUS_LABELS[status] }}</span
    >
  </AttributeRow>
  <AttributeRow label="document" :type="element.sbmlType" field="resolution.entry">
    <RouterLink
      v-if="entry && entryIndex"
      :to="view.routeFor(entryIndex.document.pk, { entry, model: null })"
      class="font-mono text-link hover:underline"
      data-testid="resolution-entry"
      >{{ entry }}</RouterLink
    >
    <ValueText v-else :value="entry" mono />
  </AttributeRow>
  <AttributeRow label="model" :type="element.sbmlType" field="resolution.model">
    <ElementLink
      v-if="resolution?.model"
      :pk="resolution.model"
      :entry="entry"
      mark
      data-testid="resolution-model"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="md5 check" :type="element.sbmlType" field="resolution.md5Matches">
    <span v-if="resolution?.md5Matches === true" data-testid="resolution-md5"
      >matches the document</span
    >
    <span
      v-else-if="resolution?.md5Matches === false"
      class="text-amber-700"
      data-testid="resolution-md5"
      >does not match the document</span
    >
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
