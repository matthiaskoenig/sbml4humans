<script setup lang="ts">
import type { InitialAssignment } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: InitialAssignment }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="symbol" :type="element.sbmlType" field="symbol">
    <ElementLink
      :pk="index?.resolve(element.pk, 'symbol', element.symbol)"
      :label="element.symbol"
    />
  </AttributeRow>
  <AttributeRow label="math" :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
  <AttributeRow label="derived units" :type="element.sbmlType" field="derivedUnits"
    ><UnitsView :latex="element.derivedUnits"
  /></AttributeRow>
</template>
