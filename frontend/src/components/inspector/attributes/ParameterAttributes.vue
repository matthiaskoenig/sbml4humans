<script setup lang="ts">
import type { Parameter } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: Parameter }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="value"><ValueText :value="element.value" /></AttributeRow>
  <AttributeRow label="units">
    <span class="inline-flex items-center gap-2">
      <ElementLink
        :pk="index?.resolve(element.pk, 'units', element.units)"
        :label="element.units"
      />
      <UnitsView :latex="element.unitsLatex" />
    </span>
  </AttributeRow>
  <AttributeRow label="constant"><BooleanMark :value="element.constant" /></AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
</template>
