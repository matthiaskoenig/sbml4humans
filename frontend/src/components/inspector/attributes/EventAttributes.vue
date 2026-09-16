<script setup lang="ts">
import type { Event } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Event }>();
const index = useReportIndex();

const ASSIGNMENT_COLUMNS = [
  { key: "id", header: "id" },
  { key: "variable", header: "variable" },
  { key: "math", header: "math" },
];
</script>

<template>
  <AttributeRow label="values from trigger time"
    ><BooleanMark :value="element.useValuesFromTriggerTime"
  /></AttributeRow>
  <AttributeRow label="trigger"><MathView :math="element.trigger?.math" display /></AttributeRow>
  <AttributeRow label="trigger initial value"
    ><BooleanMark :value="element.trigger?.initialValue"
  /></AttributeRow>
  <AttributeRow label="trigger persistent"
    ><BooleanMark :value="element.trigger?.persistent"
  /></AttributeRow>
  <AttributeRow label="priority"><MathView :math="element.priority" /></AttributeRow>
  <AttributeRow label="delay"><MathView :math="element.delay" /></AttributeRow>
  <AttributeRow label="event assignments">
    <NestedTable :rows="element.listOfEventAssignments ?? []" :columns="ASSIGNMENT_COLUMNS">
      <template #cell-id="{ row }"
        ><ElementLink :pk="row.pk" :label="row.id ?? row.variable"
      /></template>
      <template #cell-variable="{ row }"
        ><ElementLink :pk="index?.resolve(row.pk, 'variable', row.variable)" :label="row.variable"
      /></template>
      <template #cell-math="{ row }"><MathView :math="row.math" /></template>
    </NestedTable>
  </AttributeRow>
</template>
