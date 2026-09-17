<script setup lang="ts">
import type { EdgeKind, Reaction } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: Reaction }>();
const index = useReportIndex();

const PARTICIPANT_COLUMNS = [
  { key: "id", header: "id" },
  { key: "species", header: "species" },
  { key: "stoichiometry", header: "stoichiometry" },
  { key: "constant", header: "constant" },
];
const MODIFIER_COLUMNS = PARTICIPANT_COLUMNS.slice(0, 2);

const species = (kind: EdgeKind, id: string) =>
  index.value?.resolve(props.element.pk, kind, id) ?? null;
</script>

<template>
  <AttributeRow label="reversible"><BooleanMark :value="element.reversible" /></AttributeRow>
  <AttributeRow label="fast"><BooleanMark :value="element.fast" /></AttributeRow>
  <AttributeRow label="compartment">
    <ElementLink
      :pk="index?.resolve(element.pk, 'compartment', element.compartment)"
      :label="element.compartment"
    />
  </AttributeRow>
  <AttributeRow label="equation"
    ><span class="font-mono">{{ element.equation }}</span></AttributeRow
  >
  <AttributeRow label="reactants">
    <NestedTable :rows="element.listOfReactants ?? []" :columns="PARTICIPANT_COLUMNS">
      <template #cell-id="{ row }"
        ><ElementLink :pk="row.pk" :label="row.id ?? row.species"
      /></template>
      <template #cell-species="{ row }"
        ><ElementLink :pk="species('reactant', row.species)" :label="row.species"
      /></template>
      <template #cell-constant="{ row }"><BooleanMark :value="row.constant" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow label="products">
    <NestedTable :rows="element.listOfProducts ?? []" :columns="PARTICIPANT_COLUMNS">
      <template #cell-id="{ row }"
        ><ElementLink :pk="row.pk" :label="row.id ?? row.species"
      /></template>
      <template #cell-species="{ row }"
        ><ElementLink :pk="species('product', row.species)" :label="row.species"
      /></template>
      <template #cell-constant="{ row }"><BooleanMark :value="row.constant" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow label="modifiers">
    <NestedTable :rows="element.listOfModifiers ?? []" :columns="MODIFIER_COLUMNS">
      <template #cell-id="{ row }"
        ><ElementLink :pk="row.pk" :label="row.id ?? row.species"
      /></template>
      <template #cell-species="{ row }"
        ><ElementLink :pk="species('modifier', row.species)" :label="row.species"
      /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow label="kinetic law">
    <template v-if="element.kineticLaw">
      <ElementLink :pk="element.kineticLaw.pk" :label="element.kineticLaw.id ?? 'kinetic law'" />
      <MathView :math="element.kineticLaw.math" display />
      <UnitsView :latex="element.kineticLaw.derivedUnits" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <template v-if="element.fbc">
    <AttributeRow label="lower flux bound">
      <ElementLink
        :pk="index?.resolve(element.pk, 'fluxBound', element.fbc.lowerFluxBound)"
        :label="element.fbc.lowerFluxBound"
      />
    </AttributeRow>
    <AttributeRow label="upper flux bound">
      <ElementLink
        :pk="index?.resolve(element.pk, 'fluxBound', element.fbc.upperFluxBound)"
        :label="element.fbc.upperFluxBound"
      />
    </AttributeRow>
    <AttributeRow label="gene product association"
      ><ValueText :value="element.fbc.geneProductAssociation" mono
    /></AttributeRow>
    <AttributeRow label="gene products">
      <span v-if="!element.fbc.geneProducts?.length" class="text-gray-400">-</span>
      <ElementLink
        v-for="gp in element.fbc.geneProducts"
        :key="gp"
        class="mr-2"
        :pk="index?.resolve(element.pk, 'geneProduct', gp)"
        :label="gp"
      />
    </AttributeRow>
  </template>
</template>
