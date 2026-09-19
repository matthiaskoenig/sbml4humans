<script setup lang="ts">
import type { GeneProduct } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: GeneProduct }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="label"
    ><ValueText :value="element.label" mono
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="associatedSpecies">
    <ElementLink
      :pk="index?.resolve(element.pk, 'associatedSpecies', element.associatedSpecies)"
      :label="element.associatedSpecies"
    />
  </AttributeRow>
</template>
