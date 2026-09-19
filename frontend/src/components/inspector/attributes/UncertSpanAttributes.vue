<script setup lang="ts">
import type { UncertSpan } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import UncertMeasureTable from "@/components/inspector/UncertMeasureTable.vue";
import UncertValue from "@/components/inspector/UncertValue.vue";
import DefinitionLink from "@/components/misc/DefinitionLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: UncertSpan }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="type"
    ><ValueText :value="element.type"
  /></AttributeRow>
  <!-- the four attributes of the span are one row, because they are one interval: each end is
  the number the file writes or the element it names -->
  <AttributeRow :type="element.sbmlType" field="interval"
    ><UncertValue :measure="element"
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="units">
    <UnitsLink
      :pk="index?.resolve(element.pk, 'units', element.units)"
      :label="element.units"
      :latex="null"
    />
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="definitionUrl"
    ><DefinitionLink :url="element.definitionUrl"
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="math"
    ><MathView :math="element.math"
  /></AttributeRow>
  <AttributeRow
    :type="element.sbmlType"
    field="uncertParameters"
    :wide="!!element.uncertParameters?.length"
  >
    <UncertMeasureTable :measures="element.uncertParameters ?? []" />
  </AttributeRow>
</template>
