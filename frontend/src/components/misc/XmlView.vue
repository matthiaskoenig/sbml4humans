<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{ xml: string | null | undefined }>();
const copied = ref(false);

async function copy(): Promise<void> {
  if (!props.xml) return;
  await navigator.clipboard.writeText(props.xml);
  copied.value = true;
  setTimeout(() => (copied.value = false), 1500);
}
</script>

<template>
  <div class="relative h-full" data-testid="xml-view">
    <button
      type="button"
      class="absolute top-2 right-2 rounded border border-gray-300 bg-white px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-100"
      data-testid="xml-copy"
      @click="copy"
    >
      {{ copied ? "Copied" : "Copy" }}
    </button>
    <pre class="h-full overflow-auto rounded bg-gray-50 p-3 font-mono text-xs leading-relaxed">{{
      xml ?? ""
    }}</pre>
  </div>
</template>
