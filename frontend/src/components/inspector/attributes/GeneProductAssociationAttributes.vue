<script setup lang="ts">
import type { GeneProductAssociation } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import GeneAssociationView from "@/components/misc/GeneAssociationView.vue";

defineProps<{ element: GeneProductAssociation }>();
</script>

<template>
  <AttributeRow label="association" :type="element.sbmlType" field="association">
    <GeneAssociationView v-if="element.association" :node="element.association" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
