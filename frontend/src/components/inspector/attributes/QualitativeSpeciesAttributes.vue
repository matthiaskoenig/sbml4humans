<script setup lang="ts">
import type { QualitativeSpecies } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: QualitativeSpecies }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="compartment" :type="element.sbmlType" field="compartment">
    <ElementLink
      :pk="index?.resolve(element.pk, 'compartment', element.compartment)"
      :label="element.compartment"
    />
  </AttributeRow>
  <AttributeRow label="initial level" :type="element.sbmlType" field="initialLevel"
    ><ValueText :value="element.initialLevel"
  /></AttributeRow>
  <AttributeRow label="max level" :type="element.sbmlType" field="maxLevel"
    ><ValueText :value="element.maxLevel"
  /></AttributeRow>
  <AttributeRow label="constant" :type="element.sbmlType" field="constant"
    ><BooleanMark :value="element.constant"
  /></AttributeRow>
</template>
