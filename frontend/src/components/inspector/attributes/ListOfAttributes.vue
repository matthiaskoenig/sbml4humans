<script setup lang="ts">
import type { ListOf } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: ListOf }>();
</script>

<template>
  <!-- the elements of the list are not repeated here: they are the rows of their table or of
  their owner, which the list names under "Referenced by" -->
  <AttributeRow :type="element.sbmlType" field="element"
    ><ValueText :value="element.element" mono
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="size"
    ><ValueText :value="element.size"
  /></AttributeRow>
</template>
