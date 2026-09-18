<script setup lang="ts">
import { computed } from "vue";

import type { UncertMeasure } from "@/api/types";
import NestedTable from "@/components/inspector/NestedTable.vue";
import UncertValue from "@/components/inspector/UncertValue.vue";
import DefinitionLink from "@/components/misc/DefinitionLink.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ measures: UncertMeasure[] }>();
const index = useReportIndex();

// the math of a measure stands in the place of its value: only a distribution and an external
// parameter carry math, and neither of them carries a value or a var next to it (distrib
// §3.11.6), so the table stays inside the pane of the inspector with four columns
const COLUMNS = [
  { key: "measure", header: "measure" },
  { key: "value", header: "value" },
  { key: "units", header: "units" },
  { key: "definitionUrl", header: "definition" },
];

interface MeasureRow {
  measure: UncertMeasure;
  /** How deep the measure sits: a distribution carries the parameters which define it, and
   * they are shown indented below it instead of in a table of their own (distrib §3.11.7). */
  depth: number;
}

function flatten(measures: UncertMeasure[], depth = 0): MeasureRow[] {
  return measures.flatMap((measure) => [
    { measure, depth },
    ...flatten(measure.uncertParameters ?? [], depth + 1),
  ]);
}

const rows = computed<MeasureRow[]>(() => flatten(props.measures));

/** The unit definition the units of a measure name, where they name one of the model. */
function unitsPk(measure: UncertMeasure): string | null {
  return index.value?.resolve(measure.pk, "units", measure.units) ?? null;
}
</script>

<template>
  <NestedTable :rows="rows" :columns="COLUMNS">
    <!-- the cell is inline, not a flex row, so that the type wraps below the identifier where
    the pane of the inspector is too narrow for both of them next to each other -->
    <template #cell-measure="{ row }">
      <span
        data-testid="uncert-measure"
        :data-depth="row.depth"
        :style="{ paddingLeft: `${row.depth}rem` }"
      >
        <ElementLink :pk="row.measure.pk" :label="row.measure.id ?? row.measure.type" />
        <!-- the type is what a measure is, and it stays visible where the identifier of the
        file takes its place in the link -->
        <span v-if="row.measure.id" class="ml-1.5 text-gray-500" data-testid="uncert-type">{{
          row.measure.type
        }}</span>
      </span>
    </template>
    <template #cell-value="{ row }">
      <span data-testid="uncert-value">
        <MathView v-if="row.measure.math" :math="row.measure.math" />
        <UncertValue v-else :measure="row.measure" />
      </span>
    </template>
    <template #cell-units="{ row }">
      <UnitsLink :pk="unitsPk(row.measure)" :label="row.measure.units" :latex="null" />
    </template>
    <template #cell-definitionUrl="{ row }">
      <DefinitionLink :url="row.measure.definitionUrl" />
    </template>
  </NestedTable>
</template>
