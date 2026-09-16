<script setup lang="ts">
import type { Uncertainty } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import MathView from "@/components/misc/MathView.vue";

defineProps<{ element: Uncertainty }>();

const COLUMNS = [
  { key: "type", header: "type" },
  { key: "var", header: "var" },
  { key: "value", header: "value" },
  { key: "units", header: "units" },
  { key: "definitionUrl", header: "definition" },
  { key: "math", header: "math" },
];
</script>

<template>
  <AttributeRow label="uncert parameters">
    <NestedTable :rows="element.uncertParameters ?? []" :columns="COLUMNS">
      <template #cell-definitionUrl="{ row }">
        <a
          v-if="row.definitionUrl"
          :href="row.definitionUrl"
          target="_blank"
          rel="noopener"
          class="text-link hover:underline"
          >{{ row.definitionUrl.split("/").pop() }}</a
        >
        <span v-else class="text-gray-400">-</span>
      </template>
      <template #cell-math="{ row }"><MathView :math="row.math" /></template>
    </NestedTable>
  </AttributeRow>
</template>
