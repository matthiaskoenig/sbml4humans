<script setup lang="ts">
import type { Input } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import QualSignMark from "@/components/misc/QualSignMark.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Input }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="qualitative species" :type="element.sbmlType" field="qualitativeSpecies">
    <ElementLink
      :pk="index?.resolve(element.pk, 'input', element.qualitativeSpecies)"
      :label="element.qualitativeSpecies"
    />
  </AttributeRow>
  <AttributeRow label="sign" :type="element.sbmlType" field="sign">
    <template v-if="element.sign"
      ><QualSignMark :sign="element.sign" /><span class="ml-1.5">{{ element.sign }}</span></template
    >
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="threshold level" :type="element.sbmlType" field="thresholdLevel"
    ><ValueText :value="element.thresholdLevel"
  /></AttributeRow>
  <AttributeRow label="transition effect" :type="element.sbmlType" field="transitionEffect"
    ><ValueText :value="element.transitionEffect"
  /></AttributeRow>
</template>
