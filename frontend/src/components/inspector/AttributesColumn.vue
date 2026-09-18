<script setup lang="ts">
import { computed } from "vue";

import type { SBase, SBaseRef } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: SBase }>();
const index = useReportIndex();

const component = computed(() =>
  props.element.sbmlType ? ATTRIBUTE_COMPONENTS[props.element.sbmlType] : null,
);
const sboUrl = computed(() =>
  props.element.sbo ? `https://identifiers.org/${props.element.sbo}` : null,
);
const uncertaintyColumns = [
  { key: "id", header: "id" },
  { key: "count", header: "parameters" },
];
const uncertainties = computed(() =>
  (props.element.uncertainties ?? []).map((u) => ({
    pk: u.pk,
    count: u.uncertParameters?.length ?? 0,
  })),
);

/** The element a comp sbaseRef names, in the order of the comp specification. */
function sbaseRefLabel(ref: SBaseRef): string {
  return ref.portRef ?? ref.idRef ?? ref.unitRef ?? ref.metaIdRef ?? "-";
}

const replacedBySubmodel = computed(() =>
  props.element.comp?.replacedBy
    ? (index.value?.resolve(
        props.element.pk,
        "replacedBy",
        props.element.comp.replacedBy.submodelRef,
      ) ?? null)
    : null,
);
const replacedElements = computed(() =>
  (props.element.comp?.replacedElements ?? []).map((replaced) => ({
    ...replaced,
    pk: index.value?.resolve(props.element.pk, "replacedElement", replaced.submodelRef) ?? null,
    ref: sbaseRefLabel(replaced.sbaseRef),
  })),
);
</script>

<template>
  <dl data-testid="attributes-column">
    <AttributeRow label="metaId" :type="element.sbmlType" field="metaId"
      ><ValueText :value="element.metaId" mono
    /></AttributeRow>
    <AttributeRow label="sbo" :type="element.sbmlType" field="sbo">
      <a
        v-if="sboUrl"
        :href="sboUrl"
        target="_blank"
        rel="noopener"
        class="font-mono text-link hover:underline"
        >{{ element.sbo }}</a
      >
      <span v-else class="text-gray-400">-</span>
    </AttributeRow>
    <template v-if="element.comp">
      <AttributeRow
        v-if="element.comp.replacedBy"
        label="replaced by"
        :type="element.sbmlType"
        field="comp.replacedBy"
      >
        <ElementLink :pk="replacedBySubmodel" :label="element.comp.replacedBy.submodelRef" />
        <span class="ml-2 font-mono text-gray-600">{{
          sbaseRefLabel(element.comp.replacedBy.sbaseRef)
        }}</span>
      </AttributeRow>
      <AttributeRow
        v-if="replacedElements.length"
        label="replaced elements"
        :type="element.sbmlType"
        field="comp.replacedElements"
        wide
      >
        <NestedTable
          :rows="replacedElements"
          :columns="[
            { key: 'submodelRef', header: 'submodel' },
            { key: 'ref', header: 'element' },
          ]"
        >
          <template #cell-submodelRef="{ row }"
            ><ElementLink :pk="row.pk" :label="row.submodelRef"
          /></template>
        </NestedTable>
      </AttributeRow>
    </template>
    <component :is="component" v-if="component" :element="element" />
    <AttributeRow
      v-if="uncertainties.length"
      label="uncertainties"
      :type="element.sbmlType"
      field="uncertainties"
      wide
    >
      <NestedTable :rows="uncertainties" :columns="uncertaintyColumns">
        <template #cell-id="{ row }"><ElementLink :pk="row.pk" /></template>
      </NestedTable>
    </AttributeRow>
  </dl>
</template>
