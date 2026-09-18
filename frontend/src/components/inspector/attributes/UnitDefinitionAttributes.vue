<script setup lang="ts">
import type { UnitDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import UnitsView from "@/components/misc/UnitsView.vue";

defineProps<{ element: UnitDefinition }>();
</script>

<template>
  <AttributeRow label="units" :type="element.sbmlType" field="unitsLatex"
    ><UnitsView :latex="element.unitsLatex"
  /></AttributeRow>
</template>
