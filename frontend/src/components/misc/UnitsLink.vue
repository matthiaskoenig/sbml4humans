<script setup lang="ts">
import ElementLink from "@/components/misc/ElementLink.vue";
import UnitsView from "@/components/misc/UnitsView.vue";
import { hasUnitsLatex } from "@/report/units";

defineProps<{
  pk: string | null | undefined;
  label: string | null | undefined;
  latex: string | null | undefined;
}>();
</script>

<template>
  <span class="inline-flex items-center gap-2">
    <ElementLink :pk="pk" :label="label" />
    <UnitsView v-if="hasUnitsLatex(latex)" :latex="latex" />
  </span>
</template>
