<script setup lang="ts">
import type { RateRule } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: RateRule }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="variable">
    <ElementLink
      :pk="index?.resolve(element.pk, 'variable', element.variable)"
      :label="element.variable"
    />
  </AttributeRow>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
</template>
