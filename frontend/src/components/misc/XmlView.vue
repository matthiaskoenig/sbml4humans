<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";

const props = withDefaults(
  defineProps<{ xml: string | null | undefined; emptyMessage?: string; caption?: string }>(),
  { emptyMessage: "No XML available.", caption: undefined },
);
const state = ref<"idle" | "copied" | "failed">("idle");
let reset: ReturnType<typeof setTimeout> | null = null;

async function copy(): Promise<void> {
  if (!props.xml) return;
  try {
    await navigator.clipboard.writeText(props.xml);
    state.value = "copied";
  } catch {
    state.value = "failed";
  }
  if (reset !== null) clearTimeout(reset);
  reset = setTimeout(() => (state.value = "idle"), 1500);
}

onBeforeUnmount(() => {
  if (reset !== null) clearTimeout(reset);
});
</script>

<template>
  <div class="relative flex h-full flex-col" data-testid="xml-view">
    <p v-if="!xml" class="text-sm text-gray-400">{{ emptyMessage }}</p>
    <template v-else>
      <!-- the caption says what the xml is when it is not the whole element: the document and
      the model carry their annotation element alone -->
      <p v-if="caption" class="mb-1 pr-16 text-xs text-gray-500" data-testid="xml-caption">
        {{ caption }}
      </p>
      <button
        type="button"
        class="absolute top-2 right-2 rounded border border-gray-300 bg-white px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-100"
        data-testid="xml-copy"
        @click="copy"
      >
        {{ state === "copied" ? "Copied" : state === "failed" ? "Failed" : "Copy" }}
      </button>
      <pre
        class="min-h-0 flex-1 overflow-auto rounded bg-gray-50 p-3 font-mono text-xs leading-relaxed"
        >{{ xml }}</pre>
    </template>
  </div>
</template>
