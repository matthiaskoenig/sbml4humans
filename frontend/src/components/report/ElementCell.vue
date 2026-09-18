<script setup lang="ts">
import { computed } from "vue";

import type { EventAssignment, SbmlElement, Math } from "@/api/types";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import XhtmlView from "@/components/misc/XhtmlView.vue";
import { fieldValue, type ColumnDef } from "@/report/columns";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ row: SbmlElement; column: ColumnDef }>();
const index = useReportIndex();

const value = computed(() => fieldValue(props.row, props.column.field));
const text = computed(() => (typeof value.value === "string" ? value.value : null));
// the casts live here: a union type in a template expression is read as a deprecated filter
const booleanValue = computed(() => (typeof value.value === "boolean" ? value.value : null));
const numberValue = computed(() => (typeof value.value === "number" ? value.value : null));
const mathValue = computed(() => (value.value as Math | null | undefined) ?? null);

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
</script>

<template>
  <!-- the identifier of a row carries the mark of its type, so that the tables of the rules,
  which look alike, and a row of an element without an id are told apart by the mark -->
  <span v-if="column.kind === 'id'" class="flex items-center gap-1.5">
    <TypeMark v-if="row.sbmlType" :type="row.sbmlType" />
    <span v-if="text" class="font-mono font-medium">{{ text }}</span>
    <ValueText v-else :value="text" mono />
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
  <ValueText v-else :value="text" :mono="column.field === 'equation'" />
</template>
