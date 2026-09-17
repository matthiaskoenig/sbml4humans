<script setup lang="ts">
import type { ExternalModelDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: ExternalModelDefinition }>();
</script>

<template>
  <AttributeRow label="source" :type="element.sbmlType" field="source"
    ><ValueText :value="element.source" mono
  /></AttributeRow>
  <AttributeRow label="model ref" :type="element.sbmlType" field="modelRef"
    ><ValueText :value="element.modelRef" mono
  /></AttributeRow>
</template>
