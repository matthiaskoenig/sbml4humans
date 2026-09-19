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

/** One row of a replacement: the submodel it names, and the element inside it which it replaces
 * or which replaces this element. A replacement scoped to a deletion names that deletion in the
 * place of an element, and a reference into an external model, whose document the report does
 * not read, keeps its name without a link. */
function replacementRow(
  replacement: ReplacedElement | ReplacedBy,
  kind: "replacedElement" | "replacedBy",
) {
  const submodel = index.value?.resolve(replacement.pk, kind, replacement.submodelRef) ?? null;
  const deletion =
    "deletion" in replacement && replacement.deletion
      ? (index.value?.resolve(replacement.pk, "deletion", replacement.deletion) ?? null)
      : null;
  const target = referenceTarget(index.value, replacement.pk, kind, submodel) ?? deletion;
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
        v-if="replacedBy"
        label="replaced by"
        :type="element.sbmlType"
        field="comp.replacedBy"
      >
        <ElementLink :pk="replacedBy.submodel" :label="replacedBy.submodelRef" />
        <span class="mx-1 text-gray-400">/</span>
        <ElementLink :pk="replacedBy.target" :label="replacedBy.name" />
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
            { key: 'name', header: 'element' },
          ]"
        >
          <template #cell-submodelRef="{ row }"
            ><ElementLink :pk="row.submodel" :label="row.submodelRef"
          /></template>
          <template #cell-name="{ row }"
            ><ElementLink :pk="row.target" :label="row.name"
          /></template>
        </NestedTable>
      </AttributeRow>
    </template>
    <component :is="component" v-if="component" :element="element" />
    <AttributeRow
      v-if="element.keyValuePairs?.length"
      label="key value pairs"
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
      label="uncertainties"
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
        <UncertMeasureTable :measures="uncertainty.uncertParameters ?? []" />
      </div>
    </AttributeRow>
  </dl>
</template>
