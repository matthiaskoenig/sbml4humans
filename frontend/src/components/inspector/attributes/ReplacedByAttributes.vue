<script setup lang="ts">
import { computed } from "vue";

import type { ReplacedBy } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";
import { referenceTarget } from "@/report/comp";

const props = defineProps<{ element: ReplacedBy }>();
const index = useReportIndex();

const submodel = computed(
  () => index.value?.resolve(props.element.pk, "replacedBy", props.element.submodelRef) ?? null,
);
/** The element inside the submodel which replaces the element carrying this reference. */
const target = computed(() =>
  referenceTarget(index.value, props.element.pk, "replacedBy", submodel.value),
);
</script>

<template>
  <AttributeRow label="submodel" :type="element.sbmlType" field="submodelRef"
    ><ElementLink :pk="submodel" :label="element.submodelRef"
  /></AttributeRow>
  <AttributeRow label="port ref" :type="element.sbmlType" field="portRef">
    <ElementLink
      v-if="element.portRef"
      :pk="target?.pk"
      :entry="target?.entry"
      :label="element.portRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="id ref" :type="element.sbmlType" field="idRef">
    <ElementLink
      v-if="element.idRef"
      :pk="target?.pk"
      :entry="target?.entry"
      :label="element.idRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="unit ref" :type="element.sbmlType" field="unitRef">
    <ElementLink
      v-if="element.unitRef"
      :pk="target?.pk"
      :entry="target?.entry"
      :label="element.unitRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="meta id ref" :type="element.sbmlType" field="metaIdRef">
    <ElementLink
      v-if="element.metaIdRef"
      :pk="target?.pk"
      :entry="target?.entry"
      :label="element.metaIdRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="nested reference" :type="element.sbmlType" field="sbaseRef">
    <ElementLink v-if="element.sbaseRef" :pk="element.sbaseRef.pk" mark />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
