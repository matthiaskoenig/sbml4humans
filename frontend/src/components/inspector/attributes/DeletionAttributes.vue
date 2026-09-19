<script setup lang="ts">
import { computed } from "vue";

import type { Deletion } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";
import { referenceTarget } from "@/report/comp";

const props = defineProps<{ element: Deletion }>();
const index = useReportIndex();

/** The element the deletion removes, which is an element of another entry where the submodel
 * instantiates an external model; without the document of that model it resolves to none. */
const target = computed(() => referenceTarget(index.value, props.element.pk, "deletion"));
</script>

<template>
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
