<script setup lang="ts">
import type { Species } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Species }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="compartment">
    <ElementLink
      :pk="index?.resolve(element.pk, 'compartment', element.compartment)"
      :label="element.compartment"
    />
  </AttributeRow>
  <AttributeRow label="initial amount"><ValueText :value="element.initialAmount" /></AttributeRow>
  <AttributeRow label="initial concentration"
    ><ValueText :value="element.initialConcentration"
  /></AttributeRow>
  <AttributeRow label="substance units">
    <UnitsLink
      :pk="index?.resolve(element.pk, 'units', element.substanceUnits)"
      :label="element.substanceUnits"
      :latex="element.unitsLatex"
    />
  </AttributeRow>
  <AttributeRow label="only substance units"
    ><BooleanMark :value="element.hasOnlySubstanceUnits"
  /></AttributeRow>
  <AttributeRow label="boundary condition"
    ><BooleanMark :value="element.boundaryCondition"
  /></AttributeRow>
  <AttributeRow label="constant"><BooleanMark :value="element.constant" /></AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
  <AttributeRow v-if="element.conversionFactor" label="conversion factor">
    <ElementLink
      :pk="index?.resolve(element.pk, 'conversionFactor', element.conversionFactor.sid)"
      :label="element.conversionFactor.sid"
    />
    <ValueText :value="element.conversionFactor.value" />
  </AttributeRow>
  <template v-if="element.fbc">
    <AttributeRow label="chemical formula"
      ><ValueText :value="element.fbc.chemicalFormula" mono
    /></AttributeRow>
    <AttributeRow label="charge"><ValueText :value="element.fbc.charge" /></AttributeRow>
  </template>
</template>
