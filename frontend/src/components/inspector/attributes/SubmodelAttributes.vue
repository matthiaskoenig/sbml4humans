<script setup lang="ts">
import type { Submodel } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Submodel }>();
const index = useReportIndex();

const DELETION_COLUMNS = [
  { key: "portRef", header: "port ref" },
  { key: "idRef", header: "id ref" },
  { key: "unitRef", header: "unit ref" },
  { key: "metaIdRef", header: "meta id ref" },
];
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
  <AttributeRow label="deletions" :type="element.sbmlType" field="listOfDeletions"
    ><NestedTable :rows="element.listOfDeletions ?? []" :columns="DELETION_COLUMNS"
  /></AttributeRow>
</template>
