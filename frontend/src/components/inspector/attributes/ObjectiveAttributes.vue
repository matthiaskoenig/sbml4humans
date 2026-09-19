<script setup lang="ts">
import type { Objective } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Objective }>();
const index = useReportIndex();

const COLUMNS = [
  { key: "id" },
  { key: "reaction" },
  { key: "reaction2" },
  { key: "coefficient", double: true },
  { key: "variableType" },
];
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="type"
    ><ValueText :value="element.type"
  /></AttributeRow>
  <AttributeRow
    :type="element.sbmlType"
    field="listOfFluxObjectives"
    :wide="!!element.listOfFluxObjectives?.length"
  >
    <NestedTable :rows="element.listOfFluxObjectives ?? []" :columns="COLUMNS" type="FluxObjective">
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-reaction="{ row }">
        <ElementLink
          :pk="index?.resolve(row.pk, 'fluxObjective', row.reaction)"
          :label="row.reaction"
        />
      </template>
      <template #cell-reaction2="{ row }">
        <ElementLink
          :pk="index?.resolve(row.pk, 'reaction2', row.reaction2)"
          :label="row.reaction2"
        />
      </template>
    </NestedTable>
  </AttributeRow>
</template>
