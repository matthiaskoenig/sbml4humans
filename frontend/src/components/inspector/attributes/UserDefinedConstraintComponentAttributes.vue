<script setup lang="ts">
import type { UserDefinedConstraintComponent } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: UserDefinedConstraintComponent }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="variable">
    <ElementLink
      :pk="index?.resolve(element.pk, 'variable', element.variable)"
      :label="element.variable"
    />
  </AttributeRow>
  <AttributeRow v-if="element.variable2" :type="element.sbmlType" field="variable2">
    <ElementLink
      :pk="index?.resolve(element.pk, 'variable2', element.variable2)"
      :label="element.variable2"
    />
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="coefficient">
    <ElementLink
      :pk="index?.resolve(element.pk, 'coefficient', element.coefficient)"
      :label="element.coefficient"
    />
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="variableType"
    ><ValueText :value="element.variableType"
  /></AttributeRow>
</template>
