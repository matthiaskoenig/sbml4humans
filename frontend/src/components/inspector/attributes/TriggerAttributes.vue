<script setup lang="ts">
import type { Trigger } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import MathView from "@/components/misc/MathView.vue";

defineProps<{ element: Trigger }>();
</script>

<template>
  <AttributeRow label="math" :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
  <AttributeRow label="initial value" :type="element.sbmlType" field="initialValue"
    ><BooleanMark :value="element.initialValue"
  /></AttributeRow>
  <AttributeRow label="persistent" :type="element.sbmlType" field="persistent"
    ><BooleanMark :value="element.persistent"
  /></AttributeRow>
</template>
