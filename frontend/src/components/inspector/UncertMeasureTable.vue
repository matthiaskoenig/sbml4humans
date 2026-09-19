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
import { attributeLabel } from "@/report/glossary";
import { formatNumber, toNumber } from "@/report/number";
import { columnChars, definitionLabel } from "@/report/text";

const props = defineProps<{
  measures: UncertMeasure[];
  /** The measures of every table which stands with this one, the uncertainties of one element,
   * whose columns line up with the columns of this table. */
  alignWith?: UncertMeasure[];
}>();
const index = useReportIndex();

// the math of a measure stands in the column of its value: only a distribution and an external
// parameter carry math, and only an external parameter may carry a value or a span next to it
// (distrib §3.11), so the table stays inside the pane of the inspector with four columns
const COLUMNS = [
  { key: "measure", header: "measure", field: "type" },
  { key: "value" },
  { key: "units" },
  { key: "definitionUrl" },
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

/** Whether the measure sets a value: a number, an element or an end of an interval. */
function hasValue(measure: UncertMeasure): boolean {
  if (measure.value != null || measure.var) return true;
  return (
    measure.sbmlType === "UncertSpan" &&
    (measure.valueLower != null ||
      measure.valueUpper != null ||
      !!measure.varLower ||
      !!measure.varUpper)
  );
}

/** The text a value cell shows, as long as the cell is wide: the interval of a span, the element
 * a value names, the number, or the formula of a distribution. */
function valueText(measure: UncertMeasure): string {
  const formula = measure.math?.formula ?? "";
  if (!hasValue(measure)) return formula || "-";
  let value: string;
  if (measure.sbmlType === "UncertSpan") {
    const end = (number: unknown, id: string | null | undefined) => {
      const double = toNumber(number);
      return id ?? (double === null ? "" : formatNumber(double));
    };
    const lower = end(measure.valueLower, measure.varLower);
    const upper = end(measure.valueUpper, measure.varUpper);
    value = lower && upper ? `${lower} to ${upper}` : lower ? `from ${lower}` : `to ${upper}`;
  } else {
    const double = toNumber(measure.value);
    value = measure.var ?? (double === null ? "-" : formatNumber(double));
  }
  // the math of a measure which also sets a value is shown below the value
  return formula.length > value.length ? formula : value;
}

/** The widths of the measure, the value and the units, from every table the table stands with,
 * so that the tables of the uncertainties of one element line up; the definition takes the
 * rest. A nested measure is indented by a rem, about two characters. */
const widths = computed(() => {
  const all = flatten(props.alignWith ?? props.measures);
  return {
    measure: columnChars(
      "measure",
      all.flatMap(({ measure, depth }) => {
        const indent = " ".repeat(2 * depth);
        return [`${indent}${measure.id ?? measure.type}`, `${indent}${measure.type}`];
      }),
    ),
    value: columnChars(
      "value",
      all.map(({ measure }) => valueText(measure)),
    ),
    units: columnChars(
      "units",
      all.map(({ measure }) => measure.units),
    ),
    definitionUrl: columnChars(
      attributeLabel("UncertParameter", "definitionUrl"),
      all.map(({ measure }) =>
        measure.definitionUrl ? definitionLabel(measure.definitionUrl) : null,
      ),
    ),
  };
});

/** The unit definition the units of a measure name, where they name one of the model. */
function unitsPk(measure: UncertMeasure): string | null {
  return index.value?.resolve(measure.pk, "units", measure.units) ?? null;
}
</script>

<template>
  <NestedTable :rows="rows" :columns="COLUMNS" type="UncertParameter" :widths="widths">
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
        <!-- an external parameter may carry a value or a span and a math at once (distrib
        §3.11), so the value is shown where it is set and the math below it -->
        <UncertValue v-if="hasValue(row.measure) || !row.measure.math" :measure="row.measure" />
        <MathView v-if="row.measure.math" :math="row.measure.math" />
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
