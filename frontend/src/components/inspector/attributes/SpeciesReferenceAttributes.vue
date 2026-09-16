<script setup lang="ts">
import { computed } from "vue";

import type { Reaction, SpeciesReference } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: SpeciesReference }>();
const index = useReportIndex();

/** The reaction listing the reference and the role of the reference in it. */
const parent = computed(() => {
  const modelId = index.value?.modelOf(props.element.pk);
  if (!index.value || !modelId) return null;
  for (const reaction of index.value.byType(modelId).get("Reaction") as Reaction[]) {
    if (reaction.listOfReactants?.some((r) => r.pk === props.element.pk))
      return { reaction, kind: "reactant" as const };
    if (reaction.listOfProducts?.some((r) => r.pk === props.element.pk))
      return { reaction, kind: "product" as const };
  }
  return null;
});

const speciesPk = computed(() =>
  parent.value
    ? (index.value?.resolve(parent.value.reaction.pk, parent.value.kind, props.element.species) ??
      null)
    : null,
);
</script>

<template>
  <AttributeRow label="reaction"
    ><ElementLink :pk="parent?.reaction.pk" :label="parent?.reaction.id ?? '-'"
  /></AttributeRow>
  <AttributeRow label="role">{{ parent?.kind ?? "-" }}</AttributeRow>
  <AttributeRow label="species"
    ><ElementLink :pk="speciesPk" :label="element.species"
  /></AttributeRow>
  <AttributeRow label="stoichiometry"><ValueText :value="element.stoichiometry" /></AttributeRow>
  <AttributeRow label="constant"><BooleanMark :value="element.constant" /></AttributeRow>
</template>
