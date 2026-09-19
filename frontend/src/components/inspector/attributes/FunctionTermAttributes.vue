<script setup lang="ts">
import type { FunctionTerm } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: FunctionTerm }>();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="math"
    ><MathView :math="element.math"
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="resultLevel"
    ><ValueText :value="element.resultLevel"
  /></AttributeRow>
</template>
