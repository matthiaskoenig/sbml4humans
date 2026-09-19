<script setup lang="ts">
import type { Compartment } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Compartment }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="spatialDimensions"
    ><ValueText :value="element.spatialDimensions" double
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="size"
    ><ValueText :value="element.size" double
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="units">
    <UnitsLink
      :pk="index?.resolve(element.pk, 'units', element.units)"
      :label="element.units"
      :latex="element.unitsLatex"
    />
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="constant"
    ><BooleanMark :value="element.constant"
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="derivedUnits"
    ><UnitsView :latex="element.derivedUnits"
  /></AttributeRow>
</template>
