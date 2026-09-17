<script setup lang="ts">
import { computed } from "vue";

import type { Edge, EdgeKind } from "@/api/types";
import ElementLink from "@/components/misc/ElementLink.vue";
import { EDGE_KINDS, edgeKindLabel } from "@/data/edgeKinds";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ pk: string }>();
const index = useReportIndex();

interface Group {
  kind: EdgeKind;
  label: string;
  pks: string[];
}

function group(edges: Edge[], end: "source" | "target"): Group[] {
  return EDGE_KINDS.map((kind) => ({
    kind,
    label: edgeKindLabel(kind),
    pks: [...new Set(edges.filter((edge) => edge.kind === kind).map((edge) => edge[end]))],
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
      <dl v-for="g in references" :key="g.kind" class="mb-2">
        <dt class="text-xs text-gray-500">{{ g.label }}</dt>
        <dd class="flex flex-wrap gap-1">
          <ElementLink
            v-for="targetPk in g.pks"
            :key="targetPk"
            :pk="targetPk"
            mark
            class="rounded border border-gray-200 bg-white px-1.5 py-0.5"
          />
        </dd>
      </dl>
    </section>
    <section data-testid="links-referenced-by">
      <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
        Referenced by
      </h3>
      <p v-if="referencedBy.length === 0" class="text-gray-400">none</p>
      <dl v-for="g in referencedBy" :key="g.kind" class="mb-2">
        <dt class="text-xs text-gray-500">{{ g.label }}</dt>
        <dd class="flex flex-wrap gap-1">
          <ElementLink
            v-for="sourcePk in g.pks"
            :key="sourcePk"
            :pk="sourcePk"
            mark
            class="rounded border border-gray-200 bg-white px-1.5 py-0.5"
          />
        </dd>
      </dl>
    </section>
  </div>
</template>
