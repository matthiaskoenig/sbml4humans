<script setup lang="ts">
import { computed } from "vue";

import type { Edge, EdgeKind, SbmlType } from "@/api/types";
import HelpLabel from "@/components/help/HelpLabel.vue";
import LinksGroup from "@/components/inspector/LinksGroup.vue";
import { EDGE_KINDS, edgeKindLabel } from "@/data/edgeKinds";
import { useReportIndex } from "@/report/context";
import { linkEntry, linkKey } from "@/report/glossary";
import type { CrossEdge, ElementRef } from "@/report/index";

const props = defineProps<{ pk: string }>();
const index = useReportIndex();

interface Group {
  kind: EdgeKind;
  label: string;
  refs: ElementRef[];
}

/** A kinetic law holds the formula of the speed of its reaction and a function term a row of the
 * transition table of its transition, and the graph says so: the reaction names its kinetic law
 * and the kinetic law names what its formula reads. A reader asks which reactions and which
 * transitions read a species, so the math links of the two are shown as the math of the element
 * they belong to, in both directions, the way a species reference is looked across below. The
 * kinetic law and the term keep their own links. */
const MATH_OWNER_KINDS: Partial<Record<SbmlType, EdgeKind>> = {
  KineticLaw: "kineticLaw",
  FunctionTerm: "functionTerm",
};

/** The element whose math the math of a kinetic law or of a function term is, else null. */
function mathOwner(pk: string): string | null {
  const type = index.value?.get(pk)?.sbmlType;
  const kind = type ? MATH_OWNER_KINDS[type] : undefined;
  if (!kind) return null;
  return index.value?.referencedBy(pk).find((edge) => edge.kind === kind)?.source ?? null;
}

/** The genes a reaction needs are the leaves of its gene product association, a tree the graph
 * walks from the reaction over its operators to a reference which names the gene product. A
 * reader asks "which genes does this reaction need" and "which reactions need this gene", so the
 * gene products of the tree are shown as links of the reaction and the reaction as a link of
 * every gene product, the way a species reference is looked across below. The association keeps
 * its link from the reaction, and the nodes of the tree keep their own links. */
function geneProductEdges(pk: string): Edge[] {
  if (index.value?.get(pk)?.sbmlType !== "Reaction") return [];
  return index.value
    .geneProducts(pk)
    .map((target) => ({ source: pk, target, kind: "geneProduct" as const }));
}

/** The edges from the element as its links show them: its own, the math of the kinetic law or of
 * the function terms it names, and the gene products its association names. */
function outgoing(pk: string): Edge[] {
  const own = index.value?.references(pk) ?? [];
  const math = own
    .filter((edge) => mathOwner(edge.target) === pk)
    .flatMap((edge) => index.value?.references(edge.target) ?? [])
    .filter((edge) => edge.kind === "math")
    .map((edge) => ({ ...edge, source: pk }));
  return [...own, ...math, ...geneProductEdges(pk)];
}

/** The edges to the element as its links show them: the math of a kinetic law or of a function
 * term comes from the element they belong to, and a gene product is named by the reaction whose
 * association holds the reference which names it. */
function incoming(pk: string): Edge[] {
  return (index.value?.referencedBy(pk) ?? []).map((edge) => {
    const owner =
      edge.kind === "math"
        ? mathOwner(edge.source)
        : edge.kind === "geneProduct"
          ? (index.value?.associationReaction(edge.source) ?? null)
          : null;
    return owner ? { ...edge, source: owner } : edge;
  });
}

/** A species reference stands between a reaction and a species, and the graph says so: the
 * reaction names the reference and the reference names the species. A reader of the links asks
 * the question over that hop, "which species does this reaction consume" and "which reactions
 * consume this species", so a group shows the element at the far end of the hop. The reference
 * itself keeps its links, and the attributes of a reaction list both. */
function farEnd(pk: string, kind: EdgeKind, end: "source" | "target"): string {
  const element = index.value?.get(pk);
  const type = element?.sbmlType;
  if (type !== "SpeciesReference" && type !== "ModifierSpeciesReference") return pk;
  if (end === "target") {
    const species = index.value?.references(pk).find((edge) => edge.kind === kind)?.target;
    return species ?? pk;
  }
  return index.value?.participation(pk)?.reaction ?? pk;
}

/** The groups of the links of one direction: the elements of the entry at the far end of its
 * edges, and behind them the elements of other entries, which a reference of a comp model
 * reaches through an external model definition. */
function group(edges: Edge[], across: CrossEdge[], end: "source" | "target"): Group[] {
  const inspected = index.value?.get(props.pk)?.sbmlType;
  const hop = inspected !== "SpeciesReference" && inspected !== "ModifierSpeciesReference";
  return EDGE_KINDS.map((kind) => {
    const pks = new Set(
      edges
        .filter((edge) => edge.kind === kind)
        .map((edge) => (hop ? farEnd(edge[end], kind, end) : edge[end])),
    );
    const refs: ElementRef[] = [...pks].map((pk) => ({ pk, entry: null }));
    for (const edge of across) {
      if (edge.kind !== kind) continue;
      refs.push({ pk: edge[end], entry: end === "target" ? edge.targetEntry : edge.sourceEntry });
    }
    return { kind, label: edgeKindLabel(kind), refs };
  }).filter((g) => g.refs.length > 0);
}

const references = computed(() =>
  group(outgoing(props.pk), index.value?.referencesAcross(props.pk) ?? [], "target"),
);
const referencedBy = computed(() =>
  group(incoming(props.pk), index.value?.referencedAcross(props.pk) ?? [], "source"),
);
</script>

<template>
  <div class="flex flex-col gap-4 text-sm" data-testid="links-column">
    <section data-testid="links-references">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">References</h3>
      <p v-if="references.length === 0" class="text-gray-400">none</p>
      <dl v-for="g in references" :key="g.kind" class="mb-2" :data-testid="`links-${g.kind}`">
        <dt class="text-xs text-gray-500">
          <HelpLabel :help-key="linkKey(g.kind)" :tooltip="linkEntry(g.kind)?.summary">{{
            g.label
          }}</HelpLabel>
        </dt>
        <LinksGroup :refs="g.refs" />
      </dl>
    </section>
    <section data-testid="links-referenced-by">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
        Referenced by
      </h3>
      <p v-if="referencedBy.length === 0" class="text-gray-400">none</p>
      <dl v-for="g in referencedBy" :key="g.kind" class="mb-2" :data-testid="`links-${g.kind}`">
        <dt class="text-xs text-gray-500">
          <HelpLabel :help-key="linkKey(g.kind)" :tooltip="linkEntry(g.kind)?.summary">{{
            g.label
          }}</HelpLabel>
        </dt>
        <LinksGroup :refs="g.refs" />
      </dl>
    </section>
  </div>
</template>
