<script setup lang="ts">
import type { DefaultTerm } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: DefaultTerm }>();
</script>

<template>
  <AttributeRow label="result level" :type="element.sbmlType" field="resultLevel"
    ><ValueText :value="element.resultLevel"
  /></AttributeRow>
</template>
