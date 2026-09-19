<script setup lang="ts">
import type { Priority } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";

defineProps<{ element: Priority }>();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
</template>
