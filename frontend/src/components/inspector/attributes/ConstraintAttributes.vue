<script setup lang="ts">
import type { Constraint } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: Constraint }>();
</script>

<template>
  <AttributeRow label="math" :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
  <AttributeRow label="message" :type="element.sbmlType" field="message"
    ><ValueText :value="element.message"
  /></AttributeRow>
</template>
