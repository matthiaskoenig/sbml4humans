<script setup lang="ts">
import { computed } from "vue";

import type { Submodel } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";
import { referenceName, referenceTarget } from "@/report/comp";

const props = defineProps<{ element: Submodel }>();
const index = useReportIndex();

const DELETION_COLUMNS = [
  { key: "pk", header: "deletion" },
  { key: "name", header: "element" },
];
/** Every deletion with the element it removes, which a deletion of an external model, whose
 * document the report does not read, does not resolve to. */
const deletions = computed(() =>
  (props.element.listOfDeletions ?? []).map((deletion) => {
    const target = referenceTarget(index.value, deletion.pk, "deletion");
    // the element names itself where the report resolved the reference, and the deletion keeps
    // the name of the file where it does not, which is an element of another document
    return { pk: deletion.pk, name: target ? null : referenceName(deletion), target };
  }),
);
</script>

<template>
  <AttributeRow label="model ref" :type="element.sbmlType" field="modelRef">
    <ElementLink
      :pk="index?.resolve(element.pk, 'modelRef', element.modelRef)"
      :label="element.modelRef"
    />
  </AttributeRow>
  <AttributeRow
    label="time conversion factor"
    :type="element.sbmlType"
    field="timeConversionFactor"
  >
    <ElementLink
      :pk="index?.resolve(element.pk, 'conversionFactor', element.timeConversionFactor)"
      :label="element.timeConversionFactor"
    />
  </AttributeRow>
  <AttributeRow
    label="extent conversion factor"
    :type="element.sbmlType"
    field="extentConversionFactor"
  >
    <ElementLink
      :pk="index?.resolve(element.pk, 'conversionFactor', element.extentConversionFactor)"
      :label="element.extentConversionFactor"
    />
  </AttributeRow>
  <AttributeRow
    label="deletions"
    :type="element.sbmlType"
    field="listOfDeletions"
    :wide="!!element.listOfDeletions?.length"
  >
    <NestedTable :rows="deletions" :columns="DELETION_COLUMNS">
      <template #cell-pk="{ row }"><ElementLink :pk="row.pk" mark /></template>
      <template #cell-name="{ row }"><ElementLink :pk="row.target" :label="row.name" /></template>
    </NestedTable>
  </AttributeRow>
</template>
