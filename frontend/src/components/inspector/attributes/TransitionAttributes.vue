<script setup lang="ts">
import { computed } from "vue";

import type { Math, Transition } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import QualSignMark from "@/components/misc/QualSignMark.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";
import { elementLabel } from "@/report/label";
import { columnChars } from "@/report/text";

const props = defineProps<{ element: Transition }>();
const index = useReportIndex();

const INPUT_COLUMNS = [
  { key: "id", header: "id" },
  { key: "qualitativeSpecies", header: "species" },
  { key: "sign", header: "sign" },
  { key: "thresholdLevel", header: "threshold" },
  { key: "transitionEffect", header: "effect" },
];

const OUTPUT_COLUMNS = [
  { key: "id", header: "id" },
  { key: "qualitativeSpecies", header: "species" },
  { key: "outputLevel", header: "output level" },
  { key: "transitionEffect", header: "effect" },
];

const TERM_COLUMNS = [
  { key: "term", header: "term", field: "id" },
  { key: "condition", header: "condition", field: "math" },
  { key: "resultLevel", header: "result level" },
];

/** The widths of the two columns the inputs and the outputs share, from the rows of both, so
 * that the two tables line up. */
const widths = computed(() => {
  const influences = [
    ...(props.element.listOfInputs ?? []),
    ...(props.element.listOfOutputs ?? []),
  ];
  return {
    id: columnChars(
      "id",
      influences.map((influence) => elementLabel(index.value, influence.pk)),
    ),
    qualitativeSpecies: columnChars(
      "species",
      influences.map((influence) => influence.qualitativeSpecies),
    ),
    transitionEffect: columnChars(
      "effect",
      influences.map((influence) => influence.transitionEffect),
    ),
  };
});
/** The inputs have the sign and the threshold where the outputs have their level, so the effect,
 * which both have, lines up where the output level is as wide as the two of them with the
 * padding of the second cell, 0.75rem of text of 0.75rem whose characters are 0.61 of it wide. */
const inputWidths = computed(() => ({ ...widths.value, sign: 4, thresholdLevel: 9 }));
const outputWidths = computed(() => ({ ...widths.value, outputLevel: 4 + 9 + 1 / 0.61 }));

interface TermRow {
  pk: string;
  math: Math | null | undefined;
  resultLevel: number | null | undefined;
  /** The default term has no condition: it holds wherever no function term does. */
  isDefault: boolean;
}

/** The transition table of the transition (qual §3.6.6): the function terms in the order in
 * which they are read, the first one whose condition holds deciding the level, and the default
 * term as the last row, where the condition reads "otherwise". */
const terms = computed<TermRow[]>(() => {
  const rows: TermRow[] = (props.element.listOfFunctionTerms ?? []).map((term) => ({
    pk: term.pk,
    math: term.math,
    resultLevel: term.resultLevel,
    isDefault: false,
  }));
  const fallback = props.element.defaultTerm;
  if (fallback) {
    rows.push({
      pk: fallback.pk,
      math: null,
      resultLevel: fallback.resultLevel,
      isDefault: true,
    });
  }
  return rows;
});
</script>

<template>
  <AttributeRow
    label="inputs"
    :type="element.sbmlType"
    field="listOfInputs"
    :wide="!!element.listOfInputs?.length"
  >
    <NestedTable
      :rows="element.listOfInputs ?? []"
      :columns="INPUT_COLUMNS"
      type="Input"
      :widths="inputWidths"
    >
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-qualitativeSpecies="{ row }">
        <ElementLink
          :pk="index?.resolve(row.pk, 'input', row.qualitativeSpecies)"
          :label="row.qualitativeSpecies"
        />
      </template>
      <template #cell-sign="{ row }"><QualSignMark :sign="row.sign" /></template>
      <template #cell-thresholdLevel="{ row }"><ValueText :value="row.thresholdLevel" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow
    label="outputs"
    :type="element.sbmlType"
    field="listOfOutputs"
    :wide="!!element.listOfOutputs?.length"
  >
    <NestedTable
      :rows="element.listOfOutputs ?? []"
      :columns="OUTPUT_COLUMNS"
      type="Output"
      :widths="outputWidths"
    >
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-qualitativeSpecies="{ row }">
        <ElementLink
          :pk="index?.resolve(row.pk, 'output', row.qualitativeSpecies)"
          :label="row.qualitativeSpecies"
        />
      </template>
      <template #cell-outputLevel="{ row }"><ValueText :value="row.outputLevel" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow
    label="function terms"
    :type="element.sbmlType"
    field="listOfFunctionTerms"
    :wide="!!terms.length"
  >
    <NestedTable :rows="terms" :columns="TERM_COLUMNS" type="FunctionTerm">
      <template #cell-term="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-condition="{ row }">
        <span v-if="row.isDefault" class="text-gray-500 italic">otherwise</span>
        <MathView v-else :math="row.math" />
      </template>
      <template #cell-resultLevel="{ row }"><ValueText :value="row.resultLevel" /></template>
    </NestedTable>
  </AttributeRow>
</template>
