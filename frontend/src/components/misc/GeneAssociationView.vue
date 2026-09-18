<script setup lang="ts">
import { computed } from "vue";

import type { Association } from "@/api/types";
import ElementLink from "@/components/misc/ElementLink.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { useReportIndex } from "@/report/context";
import { useLimitedList } from "@/report/limitedList";

/** One node of the gene product association of a reaction, with the nodes below it.
 *
 * The tree is written as the expression it stands for, the genes of an `and` and the
 * alternatives of an `or` in one pair of parentheses, so that a reader sees the structure the
 * way a reconstruction writes it and every gene is a link. A node with more children than the
 * list limit shows the first of them and a button for the rest: one reaction of Recon3D names
 * five thousand gene products in one `or`. */
const props = defineProps<{ node: Association }>();
const index = useReportIndex();

const children = computed<Association[]>(() =>
  props.node.sbmlType === "And" || props.node.sbmlType === "Or"
    ? (props.node.associations ?? [])
    : [],
);
// the operator carries its spaces, so that the expression reads and copies as one line;
// a template writes whitespace around an interpolation, the compiler condenses it away
const operator = computed(() => (props.node.sbmlType === "And" ? " and " : " or "));
const { shown, hiddenCount, showAll } = useLimitedList(() => children.value);

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
  <span v-else class="font-mono" data-testid="gene-association-group"
    >(<template v-for="(child, i) in shown" :key="child.pk"
      ><span v-if="i > 0" class="text-gray-500">{{ operator }}</span
      ><GeneAssociationView :node="child" /></template
    ><ShowAllButton
      v-if="hiddenCount > 0"
      :count="hiddenCount"
      class="ml-1 align-baseline"
      @click="showAll"
    />)</span
  >
</template>
