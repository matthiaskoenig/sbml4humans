<script setup lang="ts">
import type { Model } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: Model }>();
const index = useReportIndex();

const UNITS = [
  ["substanceUnits", "substanceUnitsLatex"],
  ["timeUnits", "timeUnitsLatex"],
  ["volumeUnits", "volumeUnitsLatex"],
  ["areaUnits", "areaUnitsLatex"],
  ["lengthUnits", "lengthUnitsLatex"],
  ["extentUnits", "extentUnitsLatex"],
] as const;

const resolve = (id: string | null | undefined) =>
  index.value?.resolve(props.element.pk, "units", id) ?? null;
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="kind">{{ element.kind ?? "model" }}</AttributeRow>
  <AttributeRow
    v-for="[idKey, latexKey] in UNITS"
    :key="idKey"
    :type="element.sbmlType"
    :field="idKey"
  >
    <UnitsLink :pk="resolve(element[idKey])" :label="element[idKey]" :latex="element[latexKey]" />
  </AttributeRow>
  <template v-if="element.fbc">
    <AttributeRow :type="element.sbmlType" field="fbc.strict"
      ><BooleanMark :value="element.fbc.strict"
    /></AttributeRow>
    <AttributeRow :type="element.sbmlType" field="fbc.activeObjective">
      <ElementLink
        :pk="index?.resolve(element.pk, 'activeObjective', element.fbc.activeObjective)"
        :label="element.fbc.activeObjective"
      />
    </AttributeRow>
  </template>
  <AttributeRow :type="element.sbmlType" field="conversionFactor">
    <template v-if="element.conversionFactor">
      <ElementLink
        :pk="index?.resolve(element.pk, 'conversionFactor', element.conversionFactor.sid)"
        :label="element.conversionFactor.sid"
      />
      <ValueText :value="element.conversionFactor.value" double />
      <ValueText :value="element.conversionFactor.units" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
