<script setup lang="ts">
import type { Uncertainty } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import UncertMeasureTable from "@/components/inspector/UncertMeasureTable.vue";

defineProps<{ element: Uncertainty }>();
</script>

<template>
  <AttributeRow
    :type="element.sbmlType"
    field="uncertParameters"
    :wide="!!element.uncertParameters?.length"
  >
    <UncertMeasureTable :measures="element.uncertParameters ?? []" />
  </AttributeRow>
</template>
