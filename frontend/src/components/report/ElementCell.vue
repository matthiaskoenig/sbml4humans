<script setup lang="ts">
import { computed } from "vue";

import type {
  EventAssignment,
  GeneProductAssociation,
  Input,
  Output,
  SbmlElement,
  Math,
} from "@/api/types";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import QualSignMark from "@/components/misc/QualSignMark.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import XhtmlView from "@/components/misc/XhtmlView.vue";
import { fieldValue, type ColumnDef } from "@/report/columns";
import { useReportIndex } from "@/report/context";
import { toNumber } from "@/report/number";
import { geneAssociationText } from "@/report/geneAssociation";
import { elementLabel, REPORT_NAME_HINT } from "@/report/label";

const props = defineProps<{ row: SbmlElement; column: ColumnDef }>();
const index = useReportIndex();

const value = computed(() => fieldValue(props.row, props.column.field));
const text = computed(() => (typeof value.value === "string" ? value.value : null));
// the casts live here: a union type in a template expression is read as a deprecated filter
const booleanValue = computed(() => (typeof value.value === "boolean" ? value.value : null));
// an infinite value and a NaN reach the frontend as the strings JSON has a no literal for,
// and `ValueText` renders them as the signs they stand for
const numberValue = computed(() =>
  toNumber(value.value) === null ? null : (value.value as string | number),
);
const mathValue = computed(() => (value.value as Math | null | undefined) ?? null);

/** Kind "id": the name the report gives a row the file gives no id, which is what the inspector
 * and every link call the element: the variable of a rule, the meta id of a constraint, the
 * place of an algebraic rule. */
const reportName = computed(() =>
  props.column.kind === "id" && !text.value ? elementLabel(index.value, props.row.pk) : null,
);

/** Kind "link": the pk of the referenced element, resolved through the edges of the row. */
const targetPk = computed(() =>
  props.column.link
    ? (index.value?.resolve(props.row.pk, props.column.link, text.value) ?? null)
    : null,
);

/** Kind "link" with units: the latex of the units sits next to the id. UnitsLink hides the
 * units latex entirely when it is null, empty or the report's "-" placeholder, so the id is
 * never followed by a redundant dash or a repeated id. */
const unitsLatex = computed(() => {
  if (props.column.link !== "units") return null;
  const latex = fieldValue(props.row, props.column.latexField ?? `${props.column.field}Latex`);
  return typeof latex === "string" ? latex : null;
});

/** Kind "geneAssociation": the tree of the reaction as the expression it stands for, capped at
 * the first genes so that one huge association does not fill the row. The genes are links in
 * the inspector; the cell is one line of text. */
const geneAssociation = computed(() =>
  geneAssociationText((value.value as GeneProductAssociation | null | undefined)?.association),
);

/** Kind "assignments": the event assignments of the event, an empty list when the event has
 * none, which the cell shows as the placeholder. */
const assignments = computed<EventAssignment[]>(() =>
  Array.isArray(value.value) ? (value.value as EventAssignment[]) : [],
);

/** The element an event assignment sets, resolved through the "variable" edge of the
 * assignment itself, the way the inspector of the event resolves it. */
function variablePk(assignment: EventAssignment): string | null {
  return index.value?.resolve(assignment.pk, "variable", assignment.variable) ?? null;
}

/** Kind "influence": the inputs or the outputs of a transition, an empty list where the
 * transition has none, which the cell shows as the placeholder. */
const influences = computed<(Input | Output)[]>(() =>
  Array.isArray(value.value) ? (value.value as (Input | Output)[]) : [],
);

/** The qualitative species an input or an output names, resolved through the edge of that
 * input or output, which is where the file writes the reference. */
function speciesPk(influence: Input | Output): string | null {
  if (!props.column.link) return null;
  return (
    index.value?.resolve(influence.pk, props.column.link, influence.qualitativeSpecies) ?? null
  );
}

/** The sign of an input, which an output does not carry. */
function signOf(influence: Input | Output): string | null | undefined {
  return "sign" in influence ? influence.sign : null;
}
</script>

<template>
  <!-- the identifier of a row carries the mark of its type, so that the tables of the rules,
  which look alike, are told apart by the mark; a row the file gives no id is named as the
  inspector names it, in italics, which tells that name from an id of the file -->
  <span v-if="column.kind === 'id'" class="flex items-center gap-1.5">
    <TypeMark v-if="row.sbmlType" :type="row.sbmlType" />
    <span v-if="text" class="font-mono font-medium">{{ text }}</span>
    <span
      v-else-if="reportName"
      v-tooltip.bottom="REPORT_NAME_HINT"
      class="font-mono text-gray-600 italic"
      data-testid="report-name"
      >{{ reportName }}</span
    >
    <ValueText v-else :value="null" mono />
  </span>
  <BooleanMark v-else-if="column.kind === 'boolean'" :value="booleanValue" />
  <ValueText v-else-if="column.kind === 'number' || column.kind === 'count'" :value="numberValue" />
  <MathView v-else-if="column.kind === 'math'" :math="mathValue" />
  <!-- the message of a constraint is XHTML, not text: it is rendered with the markup the notes
  are rendered with -->
  <XhtmlView v-else-if="column.kind === 'xhtml'" :xhtml="text" />
  <UnitsView v-else-if="column.kind === 'units'" :latex="text" />
  <template v-else-if="column.kind === 'link'">
    <UnitsLink v-if="column.link === 'units'" :pk="targetPk" :label="text" :latex="unitsLatex" />
    <ElementLink v-else :pk="targetPk" :label="text" />
  </template>
  <!-- the assignments of an event, on the one line of the row: "variable = math", separated by
  a comma and a space -->
  <ValueText v-else-if="column.kind === 'assignments' && !assignments.length" :value="null" />
  <span v-else-if="column.kind === 'assignments'" data-testid="assignments">
    <template v-for="(assignment, i) in assignments" :key="assignment.pk"
      ><span v-if="i > 0">, </span
      ><ElementLink :pk="variablePk(assignment)" :label="assignment.variable" /><span> = </span
      ><MathView :math="assignment.math"
    /></template>
  </span>
  <!-- the species of the inputs or of the outputs of a transition, on the one line of the row:
  the species as a link and, for an input, the sign of its influence behind it -->
  <ValueText v-else-if="column.kind === 'influence' && !influences.length" :value="null" />
  <span v-else-if="column.kind === 'influence'" data-testid="influence">
    <template v-for="(influence, i) in influences" :key="influence.pk"
      ><span v-if="i > 0">, </span
      ><ElementLink :pk="speciesPk(influence)" :label="influence.qualitativeSpecies" /><QualSignMark
        v-if="signOf(influence)"
        class="ml-0.5"
        :sign="signOf(influence)"
    /></template>
  </span>
  <!-- the expression is capped at the width of its column and cut off with an ellipsis: an
  association of a genome scale model runs over thousands of genes, and the inspector is where
  the whole tree is read -->
  <span
    v-else-if="column.kind === 'geneAssociation'"
    class="block max-w-64 truncate font-mono"
    :class="{ 'text-gray-400': !geneAssociation }"
    data-testid="gene-cell"
    >{{ geneAssociation || "-" }}</span
  >
  <!-- the equation of a reaction of a genome scale model is longer than any pane: it is capped
  at the width of its column and cut off with an ellipsis, and the inspector shows it whole -->
  <span v-else-if="column.field === 'equation'" class="block max-w-96 truncate font-mono">{{
    text
  }}</span>
  <ValueText v-else :value="text" />
</template>
