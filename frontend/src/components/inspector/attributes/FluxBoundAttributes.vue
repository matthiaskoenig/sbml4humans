<script setup lang="ts">
import type { FluxBound } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: FluxBound }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="reaction" :type="element.sbmlType" field="reaction">
    <ElementLink
      :pk="index?.resolve(element.pk, 'fluxBound', element.reaction)"
      :label="element.reaction"
    />
  </AttributeRow>
  <AttributeRow label="operation" :type="element.sbmlType" field="operation"
    ><ValueText :value="element.operation" mono
  /></AttributeRow>
  <AttributeRow label="value" :type="element.sbmlType" field="value"
    ><ValueText :value="element.value" double
  /></AttributeRow>
</template>
