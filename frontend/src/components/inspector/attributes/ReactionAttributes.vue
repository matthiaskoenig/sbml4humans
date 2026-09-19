<script setup lang="ts">
import { computed } from "vue";

import type { EdgeKind, Reaction } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import GeneAssociationView from "@/components/misc/GeneAssociationView.vue";
import MathView from "@/components/misc/MathView.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import { useReportIndex } from "@/report/context";
import { elementLabel } from "@/report/label";
import { formatNumber, toNumber } from "@/report/number";
import { columnChars } from "@/report/text";

const props = defineProps<{ element: Reaction }>();
const index = useReportIndex();

const PARTICIPANT_COLUMNS = [
  { key: "id", header: "id" },
  { key: "species", header: "species" },
  { key: "stoichiometry", header: "stoichiometry", double: true },
  { key: "constant", header: "constant" },
];
const MODIFIER_COLUMNS = PARTICIPANT_COLUMNS.slice(0, 2);

/** The widths of the columns the reactants, the products and the modifiers share, from the rows
 * of all three, so that the three tables line up; the last column of each takes the rest. */
const widths = computed(() => {
  const references = [
    ...(props.element.listOfReactants ?? []),
    ...(props.element.listOfProducts ?? []),
    ...(props.element.listOfModifiers ?? []),
  ];
  const stoichiometries = [
    ...(props.element.listOfReactants ?? []),
    ...(props.element.listOfProducts ?? []),
  ].map((reference) => {
    const value = toNumber(reference.stoichiometry);
    return value === null ? null : formatNumber(value);
  });
  return {
    id: columnChars(
      "id",
      references.map((reference) => elementLabel(index.value, reference.pk)),
    ),
    species: columnChars(
      "species",
      references.map((reference) => reference.species),
    ),
    stoichiometry: columnChars("stoichiometry", stoichiometries),
  };
});
const modifierWidths = computed(() => ({ id: widths.value.id }));

/** The species a participant of the reaction names, resolved through the edge of the species
 * reference itself, which is where the reference to the species is. */
const species = (referencePk: string, kind: EdgeKind, id: string) =>
  index.value?.resolve(referencePk, kind, id) ?? null;
</script>

<template>
  <AttributeRow label="reversible" :type="element.sbmlType" field="reversible"
    ><BooleanMark :value="element.reversible"
  /></AttributeRow>
  <AttributeRow label="fast" :type="element.sbmlType" field="fast"
    ><BooleanMark :value="element.fast"
  /></AttributeRow>
  <AttributeRow label="compartment" :type="element.sbmlType" field="compartment">
    <ElementLink
      :pk="index?.resolve(element.pk, 'compartment', element.compartment)"
      :label="element.compartment"
    />
  </AttributeRow>
  <AttributeRow label="equation" :type="element.sbmlType" field="equation"
    ><span class="font-mono">{{ element.equation }}</span></AttributeRow
  >
  <AttributeRow
    label="reactants"
    :type="element.sbmlType"
    field="listOfReactants"
    :wide="!!element.listOfReactants?.length"
  >
    <NestedTable
      :rows="element.listOfReactants ?? []"
      :columns="PARTICIPANT_COLUMNS"
      type="SpeciesReference"
      :widths="widths"
    >
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-species="{ row }"
        ><ElementLink :pk="species(row.pk, 'reactant', row.species)" :label="row.species"
      /></template>
      <template #cell-constant="{ row }"><BooleanMark :value="row.constant" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow
    label="products"
    :type="element.sbmlType"
    field="listOfProducts"
    :wide="!!element.listOfProducts?.length"
  >
    <NestedTable
      :rows="element.listOfProducts ?? []"
      :columns="PARTICIPANT_COLUMNS"
      type="SpeciesReference"
      :widths="widths"
    >
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-species="{ row }"
        ><ElementLink :pk="species(row.pk, 'product', row.species)" :label="row.species"
      /></template>
      <template #cell-constant="{ row }"><BooleanMark :value="row.constant" /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow
    label="modifiers"
    :type="element.sbmlType"
    field="listOfModifiers"
    :wide="!!element.listOfModifiers?.length"
  >
    <NestedTable
      :rows="element.listOfModifiers ?? []"
      :columns="MODIFIER_COLUMNS"
      type="ModifierSpeciesReference"
      :widths="modifierWidths"
    >
      <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      <template #cell-species="{ row }"
        ><ElementLink :pk="species(row.pk, 'modifier', row.species)" :label="row.species"
      /></template>
    </NestedTable>
  </AttributeRow>
  <AttributeRow label="kinetic law" :type="element.sbmlType" field="kineticLaw">
    <template v-if="element.kineticLaw">
      <ElementLink :pk="element.kineticLaw.pk" />
      <MathView :math="element.kineticLaw.math" display />
      <UnitsView :latex="element.kineticLaw.derivedUnits" />
    </template>
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <template v-if="element.fbc">
    <AttributeRow label="lower flux bound" :type="element.sbmlType" field="fbc.lowerFluxBound">
      <ElementLink
        :pk="index?.resolve(element.pk, 'lowerFluxBound', element.fbc.lowerFluxBound)"
        :label="element.fbc.lowerFluxBound"
      />
    </AttributeRow>
    <AttributeRow label="upper flux bound" :type="element.sbmlType" field="fbc.upperFluxBound">
      <ElementLink
        :pk="index?.resolve(element.pk, 'upperFluxBound', element.fbc.upperFluxBound)"
        :label="element.fbc.upperFluxBound"
      />
    </AttributeRow>
    <AttributeRow
      label="gene product association"
      :type="element.sbmlType"
      field="fbc.geneProductAssociation"
    >
      <template v-if="element.fbc.geneProductAssociation">
        <ElementLink :pk="element.fbc.geneProductAssociation.pk" class="mr-2" />
        <GeneAssociationView
          v-if="element.fbc.geneProductAssociation.association"
          :node="element.fbc.geneProductAssociation.association"
        />
      </template>
      <span v-else class="text-gray-400">-</span>
    </AttributeRow>
  </template>
</template>
