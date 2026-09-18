<script setup lang="ts">
import type { FluxObjective } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: FluxObjective }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="reaction" :type="element.sbmlType" field="reaction">
    <ElementLink
      :pk="index?.resolve(element.pk, 'fluxObjective', element.reaction)"
      :label="element.reaction"
    />
  </AttributeRow>
  <AttributeRow
    v-if="element.reaction2"
    label="second reaction"
    :type="element.sbmlType"
    field="reaction2"
  >
    <ElementLink
      :pk="index?.resolve(element.pk, 'reaction2', element.reaction2)"
      :label="element.reaction2"
    />
  </AttributeRow>
  <AttributeRow label="coefficient" :type="element.sbmlType" field="coefficient"
    ><ValueText :value="element.coefficient"
  /></AttributeRow>
  <AttributeRow label="variable type" :type="element.sbmlType" field="variableType"
    ><ValueText :value="element.variableType"
  /></AttributeRow>
</template>
