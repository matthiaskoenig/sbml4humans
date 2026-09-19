<script setup lang="ts">
import { computed } from "vue";

import type { ReplacedBy, ReplacedElement, SBase } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import UncertMeasureTable from "@/components/inspector/UncertMeasureTable.vue";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { referenceName, referenceTarget } from "@/report/comp";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: SBase }>();
const index = useReportIndex();

const component = computed(() =>
  props.element.sbmlType ? ATTRIBUTE_COMPONENTS[props.element.sbmlType] : null,
);
const sboUrl = computed(() =>
  props.element.sbo ? `https://identifiers.org/${props.element.sbo}` : null,
);
const keyValueColumns = [
  { key: "key", header: "key" },
  { key: "value", header: "value" },
  { key: "uri", header: "uri" },
];

/** The measures of every uncertainty of the element, whose tables line up with each other. */
const allMeasures = computed(() =>
  (props.element.uncertainties ?? []).flatMap((uncertainty) => uncertainty.uncertParameters ?? []),
);

/** One row of a replacement: the submodel it names, and the element inside it which it replaces
 * or which replaces this element. A replacement scoped to a deletion names that deletion in the
 * place of an element, a reference into an external model ends at the element of another entry
 * of the archive, and one into a document the report does not have keeps its name without a
 * link. */
function replacementRow(
  replacement: ReplacedElement | ReplacedBy,
  kind: "replacedElement" | "replacedBy",
) {
  const submodel = index.value?.resolve(replacement.pk, kind, replacement.submodelRef) ?? null;
  const deletion =
    "deletion" in replacement && replacement.deletion
      ? (index.value?.resolve(replacement.pk, "deletion", replacement.deletion) ?? null)
      : null;
  const target =
    referenceTarget(index.value, replacement.pk, kind, submodel) ??
    (deletion ? { pk: deletion, entry: null } : null);
  const name =
    referenceName(replacement) ??
    ("deletion" in replacement ? (replacement.deletion ?? null) : null);
  // the element names itself where the report resolved the reference, and the reference keeps
  // the name of the file where it does not, which is the port or the id of another document
  return {
    pk: replacement.pk,
    submodelRef: replacement.submodelRef,
    submodel,
    name: target ? null : name,
    target,
  };
}

const replacedBy = computed(() =>
  props.element.comp?.replacedBy
    ? replacementRow(props.element.comp.replacedBy, "replacedBy")
    : null,
);
const replacedElements = computed(() =>
  (props.element.comp?.replacedElements ?? []).map((replaced) =>
    replacementRow(replaced, "replacedElement"),
  ),
);
</script>

<template>
  <!-- the two columns of every row: the labels, as wide as the longest of them and never more
  than half of the pane, and the values with the rest -->
  <dl
    class="grid grid-cols-[fit-content(50%)_minmax(0,1fr)] gap-x-3"
    data-testid="attributes-column"
  >
    <AttributeRow :type="element.sbmlType" field="metaId"
      ><ValueText :value="element.metaId" mono
    /></AttributeRow>
    <AttributeRow :type="element.sbmlType" field="sbo">
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
      <AttributeRow v-if="replacedBy" :type="element.sbmlType" field="comp.replacedBy">
        <ElementLink :pk="replacedBy.submodel" :label="replacedBy.submodelRef" />
        <span class="mx-1 text-gray-400">/</span>
        <ElementLink
          :pk="replacedBy.target?.pk"
          :entry="replacedBy.target?.entry"
          :label="replacedBy.name"
        />
      </AttributeRow>
      <AttributeRow
        v-if="replacedElements.length"
        :type="element.sbmlType"
        field="comp.replacedElements"
        wide
      >
        <NestedTable
          :rows="replacedElements"
          type="ReplacedElement"
          :columns="[{ key: 'submodelRef' }, { key: 'name', header: 'element' }]"
        >
          <template #cell-submodelRef="{ row }"
            ><ElementLink :pk="row.submodel" :label="row.submodelRef"
          /></template>
          <template #cell-name="{ row }"
            ><ElementLink :pk="row.target?.pk" :entry="row.target?.entry" :label="row.name"
          /></template>
        </NestedTable>
      </AttributeRow>
    </template>
    <component :is="component" v-if="component" :element="element" />
    <!-- a list which states something of its own is an element, and its owner is where a reader
    finds it: the empty list of rules of a model has no table which could name it -->
    <AttributeRow v-if="element.lists?.length" :type="element.sbmlType" field="lists">
      <div class="flex flex-wrap gap-1" data-testid="lists">
        <ElementLink
          v-for="list in element.lists"
          :key="list.pk"
          :pk="list.pk"
          mark
          class="rounded border border-gray-200 bg-white px-1.5 py-0.5"
        />
      </div>
    </AttributeRow>
    <AttributeRow
      v-if="element.keyValuePairs?.length"
      :type="element.sbmlType"
      field="keyValuePairs"
      wide
    >
      <NestedTable :rows="element.keyValuePairs" :columns="keyValueColumns">
        <template #cell-uri="{ row }">
          <a
            v-if="row.uri"
            :href="row.uri"
            target="_blank"
            rel="noopener"
            class="text-link hover:underline"
            >{{ row.uri }}</a
          >
          <span v-else class="text-gray-400">-</span>
        </template>
      </NestedTable>
    </AttributeRow>
    <!-- how well a value is known belongs next to the value: every uncertainty of the element
    is named with a link to it and shows the measures it collects, the table its own inspector
    shows -->
    <AttributeRow
      v-if="element.uncertainties?.length"
      :type="element.sbmlType"
      field="uncertainties"
      wide
    >
      <div
        v-for="uncertainty in element.uncertainties"
        :key="uncertainty.pk"
        class="mb-2 last:mb-0"
        data-testid="uncertainty"
      >
        <p class="mb-0.5" data-testid="uncertainty-name">
          <ElementLink :pk="uncertainty.pk" />
          <span v-if="uncertainty.name" class="ml-1.5 text-gray-700">{{ uncertainty.name }}</span>
        </p>
        <UncertMeasureTable
          :measures="uncertainty.uncertParameters ?? []"
          :align-with="allMeasures"
        />
      </div>
    </AttributeRow>
  </dl>
</template>
