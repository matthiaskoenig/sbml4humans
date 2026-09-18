<script setup lang="ts">
import type { UnitDefinition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import UnitsView from "@/components/misc/UnitsView.vue";

defineProps<{ element: UnitDefinition }>();

const UNIT_COLUMNS = [
  { key: "kind", header: "kind" },
  { key: "exponent", header: "exponent" },
  { key: "scale", header: "scale" },
  { key: "multiplier", header: "multiplier" },
];
</script>

<template>
  <!-- the formula the report renders from the units comes first, it is what the definition
  means; the units below it are what the file writes, so a reader can check one against the
  other -->
  <AttributeRow label="formula" :type="element.sbmlType" field="unitsLatex"
    ><UnitsView :latex="element.unitsLatex"
  /></AttributeRow>
  <AttributeRow
    label="units"
    :type="element.sbmlType"
    field="listOfUnits"
    :wide="!!element.listOfUnits?.length"
  >
    <NestedTable :rows="element.listOfUnits ?? []" :columns="UNIT_COLUMNS" />
  </AttributeRow>
</template>
