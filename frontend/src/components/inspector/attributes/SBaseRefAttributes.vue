<script setup lang="ts">
import type { SBaseRef } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ element: SBaseRef }>();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="portRef"
    ><ValueText :value="element.portRef" mono
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="idRef"
    ><ValueText :value="element.idRef" mono
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="unitRef"
    ><ValueText :value="element.unitRef" mono
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="metaIdRef"
    ><ValueText :value="element.metaIdRef" mono
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="sbaseRef">
    <ElementLink v-if="element.sbaseRef" :pk="element.sbaseRef.pk" mark />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
