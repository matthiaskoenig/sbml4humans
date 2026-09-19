<script setup lang="ts">
import type { Port } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { referenceTarget } from "@/report/comp";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: Port }>();
const index = useReportIndex();

/** The one port edge of the port; ports reference exactly one element, which a port with a
 * nested reference may name inside a submodel, and with it in another entry of the archive. */
const target = () => referenceTarget(index.value, props.element.pk, "port");
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="portRef">
    <ElementLink
      v-if="element.portRef"
      :pk="target()?.pk"
      :entry="target()?.entry"
      :label="element.portRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="idRef">
    <ElementLink
      v-if="element.idRef"
      :pk="target()?.pk"
      :entry="target()?.entry"
      :label="element.idRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="unitRef">
    <ElementLink
      v-if="element.unitRef"
      :pk="target()?.pk"
      :entry="target()?.entry"
      :label="element.unitRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="metaIdRef">
    <ElementLink
      v-if="element.metaIdRef"
      :pk="target()?.pk"
      :entry="target()?.entry"
      :label="element.metaIdRef"
    />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="sbaseRef">
    <ElementLink v-if="element.sbaseRef" :pk="element.sbaseRef.pk" mark />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
