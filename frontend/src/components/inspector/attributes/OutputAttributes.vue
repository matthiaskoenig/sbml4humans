<script setup lang="ts">
import type { Output } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Output }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="qualitative species" :type="element.sbmlType" field="qualitativeSpecies">
    <ElementLink
      :pk="index?.resolve(element.pk, 'output', element.qualitativeSpecies)"
      :label="element.qualitativeSpecies"
    />
  </AttributeRow>
  <AttributeRow label="output level" :type="element.sbmlType" field="outputLevel"
    ><ValueText :value="element.outputLevel"
  /></AttributeRow>
  <AttributeRow label="transition effect" :type="element.sbmlType" field="transitionEffect"
    ><ValueText :value="element.transitionEffect"
  /></AttributeRow>
</template>
