<script setup lang="ts">
import { computed } from "vue";

import type { SbmlElement, Math } from "@/api/types";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { fieldValue, type ColumnDef } from "@/report/columns";
import { useReportIndex } from "@/report/context";

/** The report writes the reaction equation with numeric character references (`&#10142;`
 * for the arrow), which read as markup in a text cell. */
function decodeReferences(value: string): string {
  return value.replace(/&#(\d+);/g, (_, code: string) => String.fromCodePoint(Number(code)));
}

/** "-" is the report's latex of a dimensionless or missing unit: render the placeholder
 * of an empty cell instead of a KaTeX minus. */
function unitsOf(latex: unknown): string | null {
  return typeof latex === "string" && latex !== "" && latex !== "-" ? latex : null;
}

const props = defineProps<{ row: SbmlElement; column: ColumnDef }>();
const index = useReportIndex();

const value = computed(() => fieldValue(props.row, props.column.field));
const text = computed(() => (typeof value.value === "string" ? value.value : null));
const displayText = computed(() => (text.value === null ? null : decodeReferences(text.value)));
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

/** Kind "link" with units: the latex of the units sits next to the id. */
const unitsLatex = computed(() => {
  if (props.column.link !== "units") return null;
  const latex = fieldValue(
    props.row,
    props.column.field === "units" || props.column.field === "substanceUnits"
      ? "unitsLatex"
      : `${props.column.field}Latex`,
  );
  return unitsOf(latex);
});
</script>

<template>
  <template v-if="column.kind === 'id'">
    <span class="font-mono font-medium">{{ text ?? "-" }}</span>
  </template>
  <BooleanMark v-else-if="column.kind === 'boolean'" :value="booleanValue" />
  <ValueText v-else-if="column.kind === 'number' || column.kind === 'count'" :value="numberValue" />
  <MathView v-else-if="column.kind === 'math'" :math="mathValue" />
  <UnitsView v-else-if="column.kind === 'units'" :latex="unitsOf(text)" />
  <template v-else-if="column.kind === 'link'">
    <span v-if="unitsLatex" class="inline-flex items-center gap-2">
      <ElementLink :pk="targetPk" :label="text" />
      <UnitsView :latex="unitsLatex" :units="text" />
    </span>
    <ElementLink v-else :pk="targetPk" :label="text" />
  </template>
  <ValueText v-else :value="displayText" :mono="column.field === 'equation'" />
</template>
