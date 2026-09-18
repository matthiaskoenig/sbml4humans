<script setup lang="ts">
import type { UncertParameter } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import UncertMeasureTable from "@/components/inspector/UncertMeasureTable.vue";
import DefinitionLink from "@/components/misc/DefinitionLink.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: UncertParameter }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="type" :type="element.sbmlType" field="type"
    ><ValueText :value="element.type"
  /></AttributeRow>
  <AttributeRow label="value" :type="element.sbmlType" field="value"
    ><ValueText :value="element.value"
  /></AttributeRow>
  <AttributeRow label="var" :type="element.sbmlType" field="var">
    <ElementLink :pk="index?.resolve(element.pk, 'var', element.var)" :label="element.var" />
  </AttributeRow>
  <AttributeRow label="units" :type="element.sbmlType" field="units">
    <UnitsLink
      :pk="index?.resolve(element.pk, 'units', element.units)"
      :label="element.units"
      :latex="null"
    />
  </AttributeRow>
  <AttributeRow label="definition" :type="element.sbmlType" field="definitionUrl"
    ><DefinitionLink :url="element.definitionUrl"
  /></AttributeRow>
  <AttributeRow label="math" :type="element.sbmlType" field="math"
    ><MathView :math="element.math"
  /></AttributeRow>
  <AttributeRow
    label="uncert parameters"
    :type="element.sbmlType"
    field="uncertParameters"
    :wide="!!element.uncertParameters?.length"
  >
    <UncertMeasureTable :measures="element.uncertParameters ?? []" />
  </AttributeRow>
</template>
