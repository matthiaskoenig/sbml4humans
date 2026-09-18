<script setup lang="ts">
import { computed } from "vue";

import type { UncertMeasure } from "@/api/types";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ measure: UncertMeasure }>();
const index = useReportIndex();

/** A span carries the two ends of an interval in the place of the single value of a parameter
 * (distrib §3.12). An end the file leaves out leaves the interval open at that side, which the
 * report reads as "from 1" and "to 4" instead of "1 to 4". */
const span = computed(() => (props.measure.sbmlType === "UncertSpan" ? props.measure : null));
const hasLower = computed(
  () => !!span.value && (span.value.valueLower != null || !!span.value.varLower),
);
const hasUpper = computed(
  () => !!span.value && (span.value.valueUpper != null || !!span.value.varUpper),
);

/** The element an end of a span or the value of a parameter names, through the "var" edge of
 * the measure itself, which is where the file writes the reference. */
function varPk(id: string | null | undefined): string | null {
  return index.value?.resolve(props.measure.pk, "var", id) ?? null;
}
</script>

<template>
  <span v-if="span" data-testid="uncert-span">
    <template v-if="hasLower || hasUpper">
      <span v-if="!hasLower" class="text-gray-500">to </span>
      <span v-else-if="!hasUpper" class="text-gray-500">from </span>
      <template v-if="hasLower">
        <ElementLink v-if="span.varLower" :pk="varPk(span.varLower)" :label="span.varLower" />
        <ValueText v-else :value="span.valueLower" />
      </template>
      <span v-if="hasLower && hasUpper" class="text-gray-500"> to </span>
      <template v-if="hasUpper">
        <ElementLink v-if="span.varUpper" :pk="varPk(span.varUpper)" :label="span.varUpper" />
        <ValueText v-else :value="span.valueUpper" />
      </template>
    </template>
    <ValueText v-else :value="null" />
  </span>
  <ElementLink v-else-if="measure.var" :pk="varPk(measure.var)" :label="measure.var" />
  <ValueText v-else :value="measure.value" />
</template>
