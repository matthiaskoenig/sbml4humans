<script setup lang="ts">
import { computed } from "vue";

import type { Deletion } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";
import { referenceTarget } from "@/report/comp";

const props = defineProps<{ element: Deletion }>();
const index = useReportIndex();

/** The element the deletion removes; a deletion of an external model resolves to none. */
const target = computed(() => referenceTarget(index.value, props.element.pk, "deletion"));
</script>

<template>
  <AttributeRow label="port ref" :type="element.sbmlType" field="portRef">
    <ElementLink v-if="element.portRef" :pk="target" :label="element.portRef" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="id ref" :type="element.sbmlType" field="idRef">
    <ElementLink v-if="element.idRef" :pk="target" :label="element.idRef" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="unit ref" :type="element.sbmlType" field="unitRef">
    <ElementLink v-if="element.unitRef" :pk="target" :label="element.unitRef" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="meta id ref" :type="element.sbmlType" field="metaIdRef">
    <ElementLink v-if="element.metaIdRef" :pk="target" :label="element.metaIdRef" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="nested reference" :type="element.sbmlType" field="sbaseRef">
    <ElementLink v-if="element.sbaseRef" :pk="element.sbaseRef.pk" mark />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
