<script setup lang="ts">
import type { ExternalModelDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: ExternalModelDefinition }>();
</script>

<template>
  <AttributeRow label="source"><ValueText :value="element.source" mono /></AttributeRow>
  <AttributeRow label="model ref"><ValueText :value="element.modelRef" mono /></AttributeRow>
</template>
