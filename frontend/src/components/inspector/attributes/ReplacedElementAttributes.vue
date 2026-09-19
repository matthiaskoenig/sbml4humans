<script setup lang="ts">
import { computed } from "vue";

import type { ReplacedElement } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";
import { referenceTarget } from "@/report/comp";

const props = defineProps<{ element: ReplacedElement }>();
const index = useReportIndex();

const submodel = computed(
  () =>
    index.value?.resolve(props.element.pk, "replacedElement", props.element.submodelRef) ?? null,
);
/** The replaced element inside the submodel; a reference into an external model, whose document
 * the report does not read, resolves to none and is shown as the name it carries. */
const target = computed(() =>
  referenceTarget(index.value, props.element.pk, "replacedElement", submodel.value),
);
</script>

<template>
  <AttributeRow label="submodel" :type="element.sbmlType" field="submodelRef"
    ><ElementLink :pk="submodel" :label="element.submodelRef"
  /></AttributeRow>
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
  <AttributeRow label="deletion" :type="element.sbmlType" field="deletion">
    <ElementLink
      v-if="element.deletion"
      :pk="index?.resolve(element.pk, 'deletion', element.deletion)"
      :label="element.deletion"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="conversion factor" :type="element.sbmlType" field="conversionFactor">
    <ElementLink
      :pk="index?.resolve(element.pk, 'conversionFactor', element.conversionFactor)"
      :label="element.conversionFactor"
    />
  </AttributeRow>
  <AttributeRow label="nested reference" :type="element.sbmlType" field="sbaseRef">
    <ElementLink v-if="element.sbaseRef" :pk="element.sbaseRef.pk" mark />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
