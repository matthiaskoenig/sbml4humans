<script setup lang="ts">
import { computed } from "vue";

import type { SpeciesReference } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";
import { parentReaction } from "@/report/parentReaction";

const props = defineProps<{ element: SpeciesReference }>();
const index = useReportIndex();

/** The reaction listing the reference and the role of the reference in it. */
const parent = computed(() => parentReaction(index.value, props.element.pk));

const speciesPk = computed(() =>
  parent.value
    ? (index.value?.resolve(parent.value.reaction.pk, parent.value.kind, props.element.species) ??
      null)
    : null,
);
</script>

<template>
  <AttributeRow label="reaction" :type="element.sbmlType" field="reaction"
    ><ElementLink :pk="parent?.reaction.pk" :label="parent?.reaction.id ?? '-'"
  /></AttributeRow>
  <AttributeRow label="role" :type="element.sbmlType" field="role">{{
    parent?.kind ?? "-"
  }}</AttributeRow>
  <AttributeRow label="species" :type="element.sbmlType" field="species"
    ><ElementLink :pk="speciesPk" :label="element.species"
  /></AttributeRow>
  <AttributeRow label="stoichiometry" :type="element.sbmlType" field="stoichiometry"
    ><ValueText :value="element.stoichiometry"
  /></AttributeRow>
  <AttributeRow label="constant" :type="element.sbmlType" field="constant"
    ><BooleanMark :value="element.constant"
  /></AttributeRow>
</template>
