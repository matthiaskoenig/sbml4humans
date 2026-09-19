<script setup lang="ts">
import { computed } from "vue";

import type { ModifierSpeciesReference } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: ModifierSpeciesReference }>();
const index = useReportIndex();

/** The reaction listing the modifier reference, read from the edge of the reaction to it. */
const parent = computed(() => index.value?.participation(props.element.pk) ?? null);

const speciesPk = computed(
  () => index.value?.resolve(props.element.pk, "modifier", props.element.species) ?? null,
);
</script>

<template>
  <AttributeRow label="reaction" :type="element.sbmlType" field="reaction"
    ><ElementLink :pk="parent?.reaction"
  /></AttributeRow>
  <AttributeRow label="species" :type="element.sbmlType" field="species"
    ><ElementLink :pk="speciesPk" :label="element.species"
  /></AttributeRow>
</template>
