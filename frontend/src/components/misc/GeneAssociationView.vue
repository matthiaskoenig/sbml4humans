<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { Association } from "@/api/types";
import ElementLink from "@/components/misc/ElementLink.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { useReportIndex } from "@/report/context";
import {
  ASSOCIATION_DEPTH,
  ASSOCIATION_FEW_GENES,
  ASSOCIATION_LIMIT,
} from "@/report/geneAssociation";
import { useLimitedList } from "@/report/limitedList";

/** One node of the gene product association of a reaction, with the nodes below it.
 *
 * The tree is written as the expression it stands for, the genes of an `and` and the
 * alternatives of an `or` in one pair of parentheses, so that a reader sees the structure the
 * way a reconstruction writes it and every gene is a link.
 *
 * Two caps keep an association of a genome scale model from filling the inspector: a group
 * shows `ASSOCIATION_LIMIT` nodes and a button for the rest, and a group deeper than
 * `ASSOCIATION_DEPTH` is a button of its own which opens it where it stands. One reaction of
 * Recon3D is an `and` of `or`s of complexes over five thousand gene products. */
const props = withDefaults(defineProps<{ node: Association; depth?: number }>(), { depth: 0 });
const index = useReportIndex();

const children = computed<Association[]>(() =>
  props.node.sbmlType === "And" || props.node.sbmlType === "Or"
    ? (props.node.associations ?? [])
    : [],
);
// the operator carries its spaces, so that the expression reads and copies as one line;
// a template writes whitespace around an interpolation, the compiler condenses it away
const operator = computed(() => (props.node.sbmlType === "And" ? " and " : " or "));
const { shown, hiddenCount, showAll } = useLimitedList(() => children.value, ASSOCIATION_LIMIT);

/** A group below the depth of the view is opened by a click, and the nodes below it are shown
 * from that depth on, so that every level is reachable one click at a time. */
const opened = ref(false);
watch(
  () => props.node,
  () => {
    opened.value = false;
  },
);
/** A group of a few genes and nothing else is written out at any depth: the button would be
 * about as wide as the genes it hides, and it adds at most that many links to the row. */
const fewGenes = computed(
  () =>
    children.value.length <= ASSOCIATION_FEW_GENES &&
    children.value.every((child) => child.sbmlType === "GeneProductRef"),
);
const collapsed = computed(
  () =>
    children.value.length > 0 &&
    props.depth > ASSOCIATION_DEPTH &&
    !fewGenes.value &&
    !opened.value,
);

/** Kind "GeneProductRef": the gene product the leaf names, over its own edge. */
const geneProduct = computed(() =>
  props.node.sbmlType === "GeneProductRef"
    ? (index.value?.resolve(props.node.pk, "geneProduct", props.node.geneProduct) ?? null)
    : null,
);
</script>

<template>
  <!-- a leaf keeps the test id of an element link: it is one, and a link of the report is
  found by that id wherever it is shown -->
  <ElementLink
    v-if="node.sbmlType === 'GeneProductRef'"
    :pk="geneProduct"
    :label="node.geneProduct"
  />
  <button
    v-else-if="collapsed"
    type="button"
    class="cursor-pointer font-mono text-link hover:underline"
    data-testid="gene-association-open"
    @click="opened = true"
    v-text="`(${operator.trim()} of ${children.length})`"
  />
  <span v-else class="font-mono" data-testid="gene-association-group"
    >(<template v-for="(child, i) in shown" :key="child.pk"
      ><span v-if="i > 0" class="text-gray-500">{{ operator }}</span
      ><GeneAssociationView :node="child" :depth="opened ? 1 : depth + 1" /></template
    ><ShowAllButton
      v-if="hiddenCount > 0"
      :count="hiddenCount"
      class="ml-1 align-baseline"
      @click="showAll"
    />)</span
  >
</template>
