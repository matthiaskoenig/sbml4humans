<script setup lang="ts">
import { computed } from "vue";

import type { Submodel } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { RESOLUTION_STATUS_LABELS } from "@/data/resolutionStatus";
import { useReportIndex } from "@/report/context";
import { referenceName, referenceTarget } from "@/report/comp";

const props = defineProps<{ element: Submodel }>();
const index = useReportIndex();

const model = computed(
  () => index.value?.resolve(props.element.pk, "modelRef", props.element.modelRef) ?? null,
);
/** The external model definition the submodel instantiates, if it is one: the model behind it
 * is one of another document, and the references into the submodel end at the submodel unless
 * the report has that document, so the submodel says how far its definition was followed. */
const external = computed(() => {
  const definition = model.value ? index.value?.get(model.value) : undefined;
  return definition?.sbmlType === "ExternalModelDefinition" ? definition : null;
});

const DELETION_COLUMNS = [
  { key: "pk", header: "deletion", field: "id" },
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
    <ElementLink :pk="model" :label="element.modelRef" />
  </AttributeRow>
  <AttributeRow
    v-if="external"
    label="external model"
    type="ExternalModelDefinition"
    field="resolution.model"
  >
    <ElementLink
      v-if="external.resolution?.model"
      :pk="external.resolution.model"
      :entry="external.resolution.entry"
      mark
    />
    <span v-else class="text-amber-700" data-testid="resolution-status">{{
      RESOLUTION_STATUS_LABELS[external.resolution?.status ?? "notFound"]
    }}</span>
  </AttributeRow>
  <AttributeRow
    label="time conversion factor"
    :type="element.sbmlType"
    field="timeConversionFactor"
  >
    <ElementLink
      :pk="index?.resolve(element.pk, 'timeConversionFactor', element.timeConversionFactor)"
      :label="element.timeConversionFactor"
    />
  </AttributeRow>
  <AttributeRow
    label="extent conversion factor"
    :type="element.sbmlType"
    field="extentConversionFactor"
  >
    <ElementLink
      :pk="index?.resolve(element.pk, 'extentConversionFactor', element.extentConversionFactor)"
      :label="element.extentConversionFactor"
    />
  </AttributeRow>
  <AttributeRow
    label="deletions"
    :type="element.sbmlType"
    field="listOfDeletions"
    :wide="!!element.listOfDeletions?.length"
  >
    <NestedTable :rows="deletions" :columns="DELETION_COLUMNS" type="Deletion">
      <template #cell-pk="{ row }"><ElementLink :pk="row.pk" mark /></template>
      <template #cell-name="{ row }"
        ><ElementLink :pk="row.target?.pk" :entry="row.target?.entry" :label="row.name"
      /></template>
    </NestedTable>
  </AttributeRow>
</template>
