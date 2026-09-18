<script setup lang="ts">
import type { And } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import GeneAssociationView from "@/components/misc/GeneAssociationView.vue";

defineProps<{ element: And }>();
</script>

<template>
  <AttributeRow label="associations" :type="element.sbmlType" field="associations">
    <GeneAssociationView :node="element" />
  </AttributeRow>
</template>
