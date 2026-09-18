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
  <AttributeRow
    label="values from trigger time"
    :type="element.sbmlType"
    field="useValuesFromTriggerTime"
    ><BooleanMark :value="element.useValuesFromTriggerTime"
  /></AttributeRow>
  <!-- the trigger, the priority and the delay are elements of their own, so every one of the
  three rows opens its element next to the formula it holds, the way the kinetic law of a
  reaction does -->
  <AttributeRow label="trigger" :type="element.sbmlType" field="trigger">
    <template v-if="element.trigger">
      <ElementLink :pk="element.trigger.pk" :label="element.trigger.id ?? 'trigger'" />
      <MathView class="ml-2" :math="element.trigger.math" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="trigger initial value" :type="element.sbmlType" field="trigger.initialValue"
    ><BooleanMark :value="element.trigger?.initialValue"
  /></AttributeRow>
  <AttributeRow label="trigger persistent" :type="element.sbmlType" field="trigger.persistent"
    ><BooleanMark :value="element.trigger?.persistent"
  /></AttributeRow>
  <AttributeRow label="priority" :type="element.sbmlType" field="priority">
    <template v-if="element.priority">
      <ElementLink :pk="element.priority.pk" :label="element.priority.id ?? 'priority'" />
      <MathView class="ml-2" :math="element.priority.math" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="delay" :type="element.sbmlType" field="delay">
    <template v-if="element.delay">
      <ElementLink :pk="element.delay.pk" :label="element.delay.id ?? 'delay'" />
      <MathView class="ml-2" :math="element.delay.math" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow
    label="event assignments"
    :type="element.sbmlType"
    field="listOfEventAssignments"
    :wide="!!element.listOfEventAssignments?.length"
  >
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
