<script setup lang="ts">
import type { SBMLDocument } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";

defineProps<{ element: SBMLDocument }>();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="level">{{ element.level }}</AttributeRow>
  <AttributeRow :type="element.sbmlType" field="version">{{ element.version }}</AttributeRow>
  <AttributeRow :type="element.sbmlType" field="packages">
    <span v-if="!element.packages?.length" class="text-gray-400">-</span>
    <span
      v-for="pkg in element.packages"
      :key="pkg.prefix"
      class="mr-1 rounded bg-gray-100 px-1.5 py-0.5 text-xs"
      >{{ pkg.prefix }} v{{ pkg.version }}</span
    >
  </AttributeRow>
</template>
