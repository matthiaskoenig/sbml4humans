<script setup lang="ts">
import { computed } from "vue";

import type { ModifierSpeciesReference } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";
import { parentReaction } from "@/report/parentReaction";

const props = defineProps<{ element: ModifierSpeciesReference }>();
const index = useReportIndex();

/** The reaction listing the modifier reference. */
const parent = computed(() => parentReaction(index.value, props.element.pk));

const speciesPk = computed(() =>
  parent.value
    ? (index.value?.resolve(parent.value.reaction.pk, "modifier", props.element.species) ?? null)
    : null,
);
</script>

<template>
  <AttributeRow label="reaction"
    ><ElementLink :pk="parent?.reaction.pk" :label="parent?.reaction.id ?? '-'"
  /></AttributeRow>
  <AttributeRow label="species"
    ><ElementLink :pk="speciesPk" :label="element.species"
  /></AttributeRow>
</template>
