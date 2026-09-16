<script setup lang="ts">
import { computed } from "vue";

import type { ModifierSpeciesReference, Reaction } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: ModifierSpeciesReference }>();
const index = useReportIndex();

/** The reaction listing the modifier reference. */
const parent = computed(() => {
  const modelId = index.value?.modelOf(props.element.pk);
  if (!index.value || !modelId) return null;
  for (const reaction of index.value.byType(modelId).get("Reaction") as Reaction[]) {
    if (reaction.listOfModifiers?.some((r) => r.pk === props.element.pk)) return reaction;
  }
  return null;
});

const speciesPk = computed(() =>
  parent.value
    ? (index.value?.resolve(parent.value.pk, "modifier", props.element.species) ?? null)
    : null,
);
</script>

<template>
  <AttributeRow label="reaction"
    ><ElementLink :pk="parent?.pk" :label="parent?.id ?? '-'"
  /></AttributeRow>
  <AttributeRow label="species"
    ><ElementLink :pk="speciesPk" :label="element.species"
  /></AttributeRow>
</template>
