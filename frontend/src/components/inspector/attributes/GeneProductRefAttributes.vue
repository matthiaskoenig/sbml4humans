<script setup lang="ts">
import type { GeneProductRef } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: GeneProductRef }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="geneProduct">
    <ElementLink
      :pk="index?.resolve(element.pk, 'geneProduct', element.geneProduct)"
      :label="element.geneProduct"
    />
  </AttributeRow>
</template>
