<script setup lang="ts">
import type { FunctionDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";

defineProps<{ element: FunctionDefinition }>();
</script>

<template>
  <AttributeRow label="math"><MathView :math="element.math" display /></AttributeRow>
</template>
