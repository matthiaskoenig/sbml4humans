<script setup lang="ts">
import type { AlgebraicRule } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";

defineProps<{ element: AlgebraicRule }>();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="derivedUnits"
    ><UnitsView :latex="element.derivedUnits"
  /></AttributeRow>
</template>
