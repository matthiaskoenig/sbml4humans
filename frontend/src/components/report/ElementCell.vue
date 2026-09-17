<script setup lang="ts">
import { computed } from "vue";

import type { SbmlElement, Math } from "@/api/types";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
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
  const latex = fieldValue(
    props.row,
    props.column.field === "units" || props.column.field === "substanceUnits"
      ? "unitsLatex"
      : `${props.column.field}Latex`,
  );
  return typeof latex === "string" ? latex : null;
});
</script>

<template>
  <template v-if="column.kind === 'id'">
    <span v-if="text" class="font-mono font-medium">{{ text }}</span>
    <ValueText v-else :value="text" mono />
  </template>
  <BooleanMark v-else-if="column.kind === 'boolean'" :value="booleanValue" />
  <ValueText v-else-if="column.kind === 'number' || column.kind === 'count'" :value="numberValue" />
  <MathView v-else-if="column.kind === 'math'" :math="mathValue" />
  <UnitsView v-else-if="column.kind === 'units'" :latex="text" />
  <template v-else-if="column.kind === 'link'">
    <UnitsLink v-if="column.link === 'units'" :pk="targetPk" :label="text" :latex="unitsLatex" />
    <ElementLink v-else :pk="targetPk" :label="text" />
  </template>
  <ValueText v-else :value="text" :mono="column.field === 'equation'" />
</template>
