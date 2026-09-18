<script setup lang="ts">
import type { Or } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import GeneAssociationView from "@/components/misc/GeneAssociationView.vue";

defineProps<{ element: Or }>();
</script>

<template>
  <AttributeRow label="associations" :type="element.sbmlType" field="associations">
    <GeneAssociationView :node="element" />
  </AttributeRow>
</template>
