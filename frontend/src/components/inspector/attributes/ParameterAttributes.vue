<script setup lang="ts">
import type { Parameter } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Parameter }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="value" :type="element.sbmlType" field="value"
    ><ValueText :value="element.value" double
  /></AttributeRow>
  <AttributeRow label="units" :type="element.sbmlType" field="units">
    <UnitsLink
      :pk="index?.resolve(element.pk, 'units', element.units)"
      :label="element.units"
      :latex="element.unitsLatex"
    />
  </AttributeRow>
  <AttributeRow label="constant" :type="element.sbmlType" field="constant"
    ><BooleanMark :value="element.constant"
  /></AttributeRow>
  <AttributeRow label="derived units" :type="element.sbmlType" field="derivedUnits"
    ><UnitsView :latex="element.derivedUnits"
  /></AttributeRow>
</template>
