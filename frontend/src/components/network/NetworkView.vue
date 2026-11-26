<script setup lang="ts">
import { CosmosViewer, type Scene } from "@graphvis/viewer";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from "vue";
import { useRouter } from "vue-router";

import type { Model } from "@/api/types";
import SelectInput from "@/components/input/SelectInput.vue";
import { conceptEntry } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import {
  buildNetwork,
  networkScene,
  networkLayout,
  type NetworkKind,
  type NetworkTheme,
} from "@/report/network";
import {
  useNetworkMetadata,
  networkLabels,
  resolvedNodeLabel,
  type NetworkLabels,
} from "@/report/network-metadata";
import { useReportView } from "@/report/view";

const props = defineProps<{ index: ReportIndex; model: Model | null }>();
const view = useReportView(),
  router = useRouter();
const container = ref<HTMLElement | null>(null);
const kind = computed({
  get: () => view.state.value.network ?? (props.model ? "base" : "all"),
  set: (value: NetworkKind) => {
    void view.setNetwork(value);
  },
});
const theme = ref<NetworkTheme>("light"),
  labelMode = ref<NetworkLabels>("name");
const layout = ref("biological"),
  spacing = ref("1");
const labels = ref(true),
  objectList = ref(false),
  query = ref("");
const status = ref("loading"),
  error = ref(""),
  hover = ref("");
const hoveredEntity = ref<string | null>(null),
  visible = shallowRef<string[]>([]);
const scene = shallowRef<Scene | null>(null);
const projection = computed(() => buildNetwork(props.index, props.model, kind.value, theme.value));
const nodes = computed(() => projection.value.nodes);
const byId = computed(() => new Map(nodes.value.map((node) => [node.id, node])));
const selected = computed(
  () =>
    nodes.value.find(
      (node) => node.pk === view.state.value.pk && node.entry === props.index.location,
    )?.id ?? view.state.value.pk,
);
const targets = computed(() => [
  ...new Set(
    [
      selected.value,
      hoveredEntity.value,
      ...(labelMode.value === "annotation" ? visible.value.slice(0, 48) : []),
    ].filter((id): id is string => !!id),
  ),
]);
const { metadata, pending } = useNetworkMetadata(nodes, targets);
const graphLabels = computed(() =>
  networkLabels(projection.value, labelMode.value, metadata.value),
);
const options = (["base", "kinetic", "all"] as const).map((value) => ({
  value,
  label: conceptEntry(`network-${value}`)!.label,
}));
const matches = computed(() => {
  const text = query.value.trim().toLowerCase();
  return nodes.value.filter(
    (node) =>
      !text ||
      `${node.label} ${node.name} ${node.sbmlType} ${resolvedNodeLabel(node, metadata.value) ?? ""}`
        .toLowerCase()
        .includes(text),
  );
});
const selectedVisible = computed(
  () =>
    !view.state.value.pk ||
    view.state.value.pk === props.model?.pk ||
    view.state.value.pk === props.index.document.pk ||
    nodes.value.some((node) => node.id === selected.value) ||
    projection.value.edges.some((edge) => (edge.entityId ?? edge.id) === selected.value),
);
let viewer: CosmosViewer | null = null,
  worker: Worker | null = null,
  generation = 0;
const positions = new Map<string, Float32Array>();

function selectEntity(id: string | null): void {
  if (!id) {
    void view.select(null);
    return;
  }
  const node = byId.value.get(id);
  if (!node) {
    if (props.index.has(id)) void view.select(id);
    return;
  }
  if (!node.inspectable) {
    hover.value = "This graph object has no SBML object in the report.";
    return;
  }
  if (
    node.entry &&
    (node.index !== props.index || (node.model && node.model !== props.model?.id))
  ) {
    void router.push(view.routeFor(node.pk, { entry: node.entry, model: node.model }));
  } else void view.select(node.pk);
}

async function rebuild(): Promise<void> {
  if (!viewer) return;
  const current = ++generation;
  worker?.terminate();
  worker = null;
  viewer.clear();
  scene.value = null;
  error.value = "";
  try {
    const packet = networkScene(projection.value, theme.value);
    packet.labels = graphLabels.value;
    if (!packet.ids.length) {
      status.value = "empty";
      return;
    }
    const key = `${packet.key}:${layout.value}:${spacing.value}`;
    const show = (xy: Float32Array) => {
      if (current !== generation || !viewer) return;
      const styled = networkScene(projection.value, theme.value);
      styled.positions = xy;
      styled.labels = graphLabels.value;
      scene.value = styled;
      void viewer.setScene(styled, { labels: labels.value });
    };
    const cached = positions.get(key);
    if (cached) {
      show(cached);
      return;
    }
    status.value = "layout";
    worker = new Worker(new URL("./layout-worker.ts", import.meta.url), { type: "module" });
    worker.onmessage = (event: MessageEvent<Float32Array>) => {
      if (current !== generation) return;
      worker?.terminate();
      worker = null;
      if (positions.size >= 12) positions.delete(positions.keys().next().value!);
      positions.set(key, event.data);
      show(event.data);
    };
    worker.onerror = () => {
      if (current !== generation) return;
      status.value = "failed";
      error.value = "The network layout could not be calculated.";
      worker?.terminate();
      worker = null;
    };
    const links = packet.links.slice(),
      hints = networkLayout(projection.value, layout.value === "biological", Number(spacing.value));
    const transfer: ArrayBuffer[] = [
      links.buffer,
      ...Object.values(hints)
        .filter((value) => value instanceof Float32Array || value instanceof Uint32Array)
        .map((value) => (value as Float32Array).buffer as ArrayBuffer),
    ];
    worker.postMessage({ count: packet.ids.length, links, options: hints }, transfer);
  } catch (cause) {
    status.value = "failed";
    error.value = cause instanceof Error ? cause.message : "The network could not be prepared.";
    worker?.terminate();
    worker = null;
  }
}

onMounted(async () => {
  await nextTick();
  if (!container.value) return;
  viewer = new CosmosViewer(container.value, {
    onSelect: selectEntity,
    onHover: (label, id) => {
      hover.value = label;
      hoveredEntity.value = id ?? null;
    },
    onVisible: (ids) => {
      visible.value = ids;
    },
    onStatus: (next, cause) => {
      status.value = next;
      if (next === "failed")
        error.value = cause instanceof Error ? cause.message : "WebGL2 could not start.";
    },
  });
  viewer.select(selected.value);
  void rebuild();
});
watch([() => props.index, () => props.model, kind], ([index], [before]) => {
  if (index !== before) positions.clear();
  if (index === before && scene.value?.key === projection.value.scope && kind.value === "all") {
    viewer?.select(selected.value);
    return;
  }
  void rebuild();
});
watch([layout, spacing], () => void rebuild());
watch(selected, (pk) => viewer?.select(pk));
watch([graphLabels, labels], () => {
  if (scene.value) {
    scene.value.labels = graphLabels.value;
    viewer?.updateLabels(graphLabels.value, labels.value);
  }
});
watch(theme, () => {
  if (!scene.value) return;
  const packet = networkScene(projection.value, theme.value);
  packet.positions = scene.value.positions;
  packet.labels = graphLabels.value;
  scene.value = packet;
  void viewer?.setScene(packet, { labels: labels.value, fit: false });
});
onBeforeUnmount(() => {
  generation++;
  worker?.terminate();
  viewer?.destroy();
  viewer = null;
  positions.clear();
});
</script>

<template>
  <section
    class="flex min-h-0 flex-1 flex-col"
    data-testid="network-view"
    aria-label="SBML network"
  >
    <div
      class="flex shrink-0 flex-wrap items-center gap-3 border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm"
    >
      <SelectInput
        :model-value="kind"
        :options="options"
        aria-label="network projection"
        data-testid="network-kind"
        @update:model-value="(value: string) => (kind = value as NetworkKind)"
      />
      <SelectInput
        v-model="layout"
        :options="[
          { value: 'biological', label: conceptEntry('network-biological-layout')!.label },
          { value: 'force', label: conceptEntry('network-force-layout')!.label },
        ]"
        aria-label="network layout"
        data-testid="network-layout"
      />
      <SelectInput
        v-model="spacing"
        :options="[
          { value: '0.8', label: 'Compact' },
          { value: '1', label: 'Balanced' },
          { value: '1.4', label: 'Spacious' },
        ]"
        aria-label="network spacing"
      />
      <SelectInput
        :model-value="theme"
        :options="[
          { value: 'light', label: 'Light' },
          { value: 'dark', label: 'Dark' },
        ]"
        aria-label="network style"
        @update:model-value="(value: string) => (theme = value as NetworkTheme)"
      />
      <SelectInput
        :model-value="labelMode"
        :options="[
          { value: 'id', label: conceptEntry('network-label-id')!.label },
          { value: 'name', label: conceptEntry('network-label-name')!.label },
          { value: 'annotation', label: conceptEntry('network-label-annotation')!.label },
        ]"
        aria-label="network label source"
        data-testid="network-label-source"
        @update:model-value="(value: string) => (labelMode = value as NetworkLabels)"
      />
      <label class="flex items-center gap-1.5"
        ><input v-model="labels" type="checkbox" data-testid="network-labels" />Labels</label
      >
      <button
        type="button"
        class="rounded border border-gray-300 bg-white px-2 py-1 hover:bg-gray-100"
        :aria-pressed="objectList"
        data-testid="network-objects-toggle"
        @click="objectList = !objectList"
      >
        Objects
      </button>
      <button
        type="button"
        class="rounded border border-gray-300 bg-white px-2 py-1 hover:bg-gray-100"
        data-testid="network-fit"
        @click="viewer?.fit()"
      >
        Fit
      </button>
      <span class="ml-auto text-gray-600" data-testid="network-counts"
        >{{ projection.nodes.length }} objects · {{ projection.edges.length }} links</span
      >
      <span v-if="pending" class="text-xs text-gray-500" data-testid="network-metadata-pending"
        >Resolving metadata…</span
      >
    </div>
    <div
      v-if="projection.unresolved.length"
      class="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900"
      role="status"
    >
      {{ projection.unresolved.length }} references could not be resolved.
    </div>
    <div
      v-if="!selectedVisible"
      class="border-b border-gray-200 px-4 py-2 text-sm text-gray-600"
      data-testid="network-selection-notice"
    >
      Selected object is outside this projection. Its details remain in the inspector.
    </div>
    <div class="relative flex min-h-0 flex-1">
      <aside
        v-if="objectList || status === 'failed'"
        class="flex w-60 shrink-0 flex-col border-r border-gray-200 bg-white max-md:w-44"
        aria-label="network objects"
      >
        <input
          v-model="query"
          type="search"
          placeholder="Find an object"
          aria-label="find network object"
          class="m-2 min-w-0 rounded border border-gray-300 px-2 py-1.5 text-sm"
          data-testid="network-search"
        />
        <div class="min-h-0 flex-1 overflow-auto">
          <button
            v-for="node in matches.slice(0, 200)"
            :key="node.id"
            type="button"
            class="block w-full border-b border-gray-100 px-3 py-2 text-left hover:bg-gray-50"
            :class="{ 'bg-selected': selected === node.id }"
            :aria-pressed="selected === node.id"
            :data-pk="node.pk"
            :data-entry="node.entry"
            data-testid="network-object"
            @click="
              selectEntity(node.id);
              viewer?.center(node.id);
            "
          >
            <span class="block truncate font-mono text-sm">{{ node.label }}</span
            ><span class="block truncate text-xs text-gray-500"
              >{{ node.sbmlType
              }}<template v-if="resolvedNodeLabel(node, metadata) || node.name">
                · {{ resolvedNodeLabel(node, metadata) || node.name }}</template
              ><template v-if="node.external"> · {{ node.entry }}</template></span
            >
          </button>
          <p v-if="matches.length > 200" class="p-3 text-sm text-gray-500">
            Showing 200 of {{ matches.length }} objects. Search to narrow the list.
          </p>
          <p v-if="!matches.length" class="p-3 text-sm text-gray-500">No objects match.</p>
        </div>
      </aside>
      <div
        ref="container"
        class="relative min-h-72 min-w-0 flex-1 overflow-hidden"
        :style="{ background: theme === 'dark' ? '#17212b' : '#ffffff' }"
        data-testid="network-canvas"
        tabindex="0"
        aria-label="Network. Select an object to inspect it. Use Objects for keyboard navigation."
        @keydown.f.prevent="viewer?.fit()"
        @keydown.+.prevent="viewer?.zoom(1.25)"
        @keydown.-.prevent="viewer?.zoom(0.8)"
      >
        <p
          v-if="status === 'empty'"
          data-testid="network-empty"
          class="absolute inset-0 flex items-center justify-center p-8 text-center text-gray-500"
        >
          This projection has no objects. Choose another projection or model.
        </p>
        <div
          v-else-if="status !== 'ready'"
          class="absolute inset-0 z-10 flex items-center justify-center p-8"
        >
          <div
            class="max-w-md rounded border border-gray-200 bg-white p-5 text-sm text-gray-700 shadow-sm"
            role="status"
            data-testid="network-status"
          >
            <template v-if="status === 'failed'"
              ><strong class="block text-gray-900">Network drawing unavailable</strong>
              <p class="mt-2">{{ error }}</p>
              <p class="mt-2">Use the object list to inspect the model, or return to Tables.</p>
              <button
                type="button"
                class="mt-3 rounded border border-gray-300 px-3 py-1"
                @click="rebuild"
              >
                Retry
              </button></template
            >
            <template v-else>{{
              status === "layout" ? "Preparing network layout…" : "Starting network renderer…"
            }}</template>
          </div>
        </div>
      </div>
      <p
        v-if="hover"
        class="pointer-events-none absolute bottom-3 left-3 max-w-[80%] truncate rounded border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-800 shadow-sm"
      >
        {{ hover }}
      </p>
    </div>
    <div
      class="flex shrink-0 flex-wrap gap-x-4 gap-y-1 border-t border-gray-200 px-4 py-1.5 text-xs text-gray-500"
    >
      <span class="inline-flex items-center gap-1.5"
        ><i class="size-2.5 rounded-full border border-slate-600 bg-slate-100" />Species</span
      >
      <span class="inline-flex items-center gap-1.5"
        ><i class="size-2.5 bg-slate-700" />Reaction</span
      >
      <span class="inline-flex items-center gap-1.5"
        ><i class="size-2.5 rotate-45 border border-blue-500 bg-blue-100" />Parameter</span
      >
      <span>Bar: inhibition</span><span>Diamond: activation</span
      ><span v-if="kind === 'all'">Dotted grey: containment</span>
      <span>Click an object or link to inspect</span
      ><span v-if="projection.nodes.length > 160 && labels">Up to 160 labels, without overlap</span>
    </div>
  </section>
</template>
