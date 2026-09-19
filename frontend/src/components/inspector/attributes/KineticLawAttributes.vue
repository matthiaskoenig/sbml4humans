<script setup lang="ts">
import type { KineticLaw } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";

defineProps<{ element: KineticLaw }>();

const COLUMNS = [
  { key: "id" },
  { key: "value", double: true },
  { key: "unitsLatex", field: "units" },
  { key: "derivedUnits" },
];
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
  <AttributeRow :type="element.sbmlType" field="derivedUnits"
    ><UnitsView :latex="element.derivedUnits"
  /></AttributeRow>
  <AttributeRow
    :type="element.sbmlType"
    field="listOfLocalParameters"
    :wide="!!element.listOfLocalParameters?.length"
  >
    <NestedTable
      :rows="element.listOfLocalParameters ?? []"
      :columns="COLUMNS"
      type="LocalParameter"
    >
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" :label="row.id" /></template>
      <template #cell-unitsLatex="{ row }"
        ><UnitsView :latex="row.unitsLatex" :units="row.units"
      /></template>
      <template #cell-derivedUnits="{ row }"><UnitsView :latex="row.derivedUnits" /></template>
    </NestedTable>
  </AttributeRow>
</template>
