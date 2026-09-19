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
  <AttributeRow label="compartment" :type="element.sbmlType" field="compartment">
    <ElementLink
      :pk="index?.resolve(element.pk, 'compartment', element.compartment)"
      :label="element.compartment"
    />
  </AttributeRow>
  <AttributeRow label="initial amount" :type="element.sbmlType" field="initialAmount"
    ><ValueText :value="element.initialAmount" double
  /></AttributeRow>
  <AttributeRow label="initial concentration" :type="element.sbmlType" field="initialConcentration"
    ><ValueText :value="element.initialConcentration" double
  /></AttributeRow>
  <AttributeRow label="substance units" :type="element.sbmlType" field="substanceUnits">
    <UnitsLink
      :pk="index?.resolve(element.pk, 'units', element.substanceUnits)"
      :label="element.substanceUnits"
      :latex="element.unitsLatex"
    />
  </AttributeRow>
  <AttributeRow label="only substance units" :type="element.sbmlType" field="hasOnlySubstanceUnits"
    ><BooleanMark :value="element.hasOnlySubstanceUnits"
  /></AttributeRow>
  <AttributeRow label="boundary condition" :type="element.sbmlType" field="boundaryCondition"
    ><BooleanMark :value="element.boundaryCondition"
  /></AttributeRow>
  <AttributeRow label="constant" :type="element.sbmlType" field="constant"
    ><BooleanMark :value="element.constant"
  /></AttributeRow>
  <AttributeRow label="derived units" :type="element.sbmlType" field="derivedUnits"
    ><UnitsView :latex="element.derivedUnits"
  /></AttributeRow>
  <AttributeRow
    v-if="element.conversionFactor"
    label="conversion factor"
    :type="element.sbmlType"
    field="conversionFactor"
  >
    <ElementLink
      :pk="index?.resolve(element.pk, 'conversionFactor', element.conversionFactor.sid)"
      :label="element.conversionFactor.sid"
    />
    <ValueText :value="element.conversionFactor.value" double />
  </AttributeRow>
  <template v-if="element.fbc">
    <AttributeRow label="chemical formula" :type="element.sbmlType" field="fbc.chemicalFormula"
      ><ValueText :value="element.fbc.chemicalFormula" mono
    /></AttributeRow>
    <AttributeRow label="charge" :type="element.sbmlType" field="fbc.charge"
      ><ValueText :value="element.fbc.charge" double
    /></AttributeRow>
  </template>
</template>
