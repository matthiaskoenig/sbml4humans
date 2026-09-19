<script setup lang="ts">
import type { UserDefinedConstraint } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: UserDefinedConstraint }>();
const index = useReportIndex();

const COLUMNS = [
  { key: "id" },
  { key: "variable" },
  { key: "variable2" },
  { key: "coefficient" },
  { key: "variableType" },
];
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="lowerBound">
    <ElementLink
      :pk="index?.resolve(element.pk, 'lowerBound', element.lowerBound)"
      :label="element.lowerBound"
    />
  </AttributeRow>
  <AttributeRow :type="element.sbmlType" field="upperBound">
    <ElementLink
      :pk="index?.resolve(element.pk, 'upperBound', element.upperBound)"
      :label="element.upperBound"
    />
  </AttributeRow>
  <AttributeRow
    :type="element.sbmlType"
    field="listOfUserDefinedConstraintComponents"
    :wide="!!element.listOfUserDefinedConstraintComponents?.length"
  >
    <NestedTable
      :rows="element.listOfUserDefinedConstraintComponents ?? []"
      :columns="COLUMNS"
      type="UserDefinedConstraintComponent"
    >
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-variable="{ row }">
        <ElementLink :pk="index?.resolve(row.pk, 'variable', row.variable)" :label="row.variable" />
      </template>
      <template #cell-variable2="{ row }">
        <ElementLink
          :pk="index?.resolve(row.pk, 'variable2', row.variable2)"
          :label="row.variable2"
        />
      </template>
      <template #cell-coefficient="{ row }">
        <ElementLink
          :pk="index?.resolve(row.pk, 'coefficient', row.coefficient)"
          :label="row.coefficient"
        />
      </template>
    </NestedTable>
  </AttributeRow>
</template>
