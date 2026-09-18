<script setup lang="ts">
import type { EventAssignment } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: EventAssignment }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="variable" :type="element.sbmlType" field="variable">
    <ElementLink
      :pk="index?.resolve(element.pk, 'variable', element.variable)"
      :label="element.variable"
    />
  </AttributeRow>
  <AttributeRow label="math" :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
</template>
