<script setup lang="ts">
import { ref } from "vue";

const props = withDefaults(
  defineProps<{ xml: string | null | undefined; emptyMessage?: string }>(),
  { emptyMessage: "No XML available." },
);
const state = ref<"idle" | "copied" | "failed">("idle");

async function copy(): Promise<void> {
  if (!props.xml) return;
  try {
    await navigator.clipboard.writeText(props.xml);
    state.value = "copied";
  } catch {
    state.value = "failed";
  }
  setTimeout(() => (state.value = "idle"), 1500);
}
</script>

<template>
  <div class="relative h-full" data-testid="xml-view">
    <p v-if="!xml" class="text-sm text-gray-400">{{ emptyMessage }}</p>
    <template v-else>
      <button
        type="button"
        class="absolute top-2 right-2 rounded border border-gray-300 bg-white px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-100"
        data-testid="xml-copy"
        @click="copy"
      >
        {{ state === "copied" ? "Copied" : state === "failed" ? "Failed" : "Copy" }}
      </button>
      <pre class="h-full overflow-auto rounded bg-gray-50 p-3 font-mono text-xs leading-relaxed">{{
        xml
      }}</pre>
    </template>
  </div>
</template>
