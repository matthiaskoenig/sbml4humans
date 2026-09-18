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
  { key: "reaction", header: "reaction" },
  { key: "coefficient", header: "coefficient" },
];
</script>

<template>
  <AttributeRow label="type" :type="element.sbmlType" field="type"
    ><ValueText :value="element.type"
  /></AttributeRow>
  <AttributeRow
    label="flux objectives"
    :type="element.sbmlType"
    field="listOfFluxObjectives"
    :wide="!!element.listOfFluxObjectives?.length"
  >
    <NestedTable :rows="element.listOfFluxObjectives ?? []" :columns="COLUMNS">
      <template #cell-reaction="{ row }">
        <ElementLink
          :pk="index?.resolve(element.pk, 'fluxObjective', row.reaction)"
          :label="row.reaction"
        />
      </template>
    </NestedTable>
  </AttributeRow>
</template>
