<script setup lang="ts">
import { ref } from "vue";

import { readStorage, writeStorage } from "@/storage";

const STORAGE_KEY = "sbml4humans.lastUrl";

const emit = defineEmits<{ submit: [url: string] }>();
const url = ref(readStorage(STORAGE_KEY) ?? "");

function submit(): void {
  const value = url.value.trim();
  if (!value) return;
  writeStorage(STORAGE_KEY, value);
  emit("submit", value);
}
</script>

<template>
  <form class="flex gap-2" @submit.prevent="submit">
    <input
      v-model="url"
      type="url"
      required
      placeholder="https://example.org/model.xml"
      class="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-link focus:outline-none"
      data-testid="url-input"
    />
    <button
      type="submit"
      class="rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
      data-testid="url-submit"
    >
      Load
    </button>
  </form>
</template>
