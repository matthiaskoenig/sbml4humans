<script setup lang="ts">
import type { LocalParameter } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import UnitsLink from "@/components/misc/UnitsLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

defineProps<{ element: LocalParameter }>();
const index = useReportIndex();
</script>

<template>
  <AttributeRow label="value"><ValueText :value="element.value" /></AttributeRow>
  <AttributeRow label="units">
    <UnitsLink
      :pk="index?.resolve(element.pk, 'units', element.units)"
      :label="element.units"
      :latex="element.unitsLatex"
    />
  </AttributeRow>
  <AttributeRow label="derived units"><UnitsView :latex="element.derivedUnits" /></AttributeRow>
</template>
