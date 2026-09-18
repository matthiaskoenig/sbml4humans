<script setup lang="ts">
import { computed } from "vue";

import type { Edge, EdgeKind } from "@/api/types";
import LinksGroup from "@/components/inspector/LinksGroup.vue";
import { EDGE_KINDS, edgeKindLabel } from "@/data/edgeKinds";
import { useReportIndex } from "@/report/context";
import { linkEntry } from "@/report/glossary";

const props = defineProps<{ pk: string }>();
const index = useReportIndex();

interface Group {
  kind: EdgeKind;
  label: string;
  pks: string[];
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

function group(edges: Edge[], end: "source" | "target"): Group[] {
  const inspected = index.value?.get(props.pk)?.sbmlType;
  const hop = inspected !== "SpeciesReference" && inspected !== "ModifierSpeciesReference";
  return EDGE_KINDS.map((kind) => ({
    kind,
    label: edgeKindLabel(kind),
    pks: [
      ...new Set(
        edges
          .filter((edge) => edge.kind === kind)
          .map((edge) => (hop ? farEnd(edge[end], kind, end) : edge[end])),
      ),
    ],
  })).filter((g) => g.pks.length > 0);
}

const references = computed(() => group(index.value?.references(props.pk) ?? [], "target"));
const referencedBy = computed(() => group(index.value?.referencedBy(props.pk) ?? [], "source"));
</script>

<template>
  <div class="flex flex-col gap-4 text-sm" data-testid="links-column">
    <section data-testid="links-references">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">References</h3>
      <p v-if="references.length === 0" class="text-gray-400">none</p>
      <dl v-for="g in references" :key="g.kind" class="mb-2" :data-testid="`links-${g.kind}`">
        <dt v-tooltip.bottom="linkEntry(g.kind)?.summary" class="text-xs text-gray-500">
          {{ g.label }}
        </dt>
        <LinksGroup :pks="g.pks" />
      </dl>
    </section>
    <section data-testid="links-referenced-by">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
        Referenced by
      </h3>
      <p v-if="referencedBy.length === 0" class="text-gray-400">none</p>
      <dl v-for="g in referencedBy" :key="g.kind" class="mb-2" :data-testid="`links-${g.kind}`">
        <dt v-tooltip.bottom="linkEntry(g.kind)?.summary" class="text-xs text-gray-500">
          {{ g.label }}
        </dt>
        <LinksGroup :pks="g.pks" />
      </dl>
    </section>
  </div>
</template>
