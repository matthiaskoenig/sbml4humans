<script setup lang="ts">
import { ref } from "vue";

import type { ApiError } from "@/api/client";

defineProps<{ error: ApiError }>();
const showTraceback = ref(false);
</script>

<template>
  <div class="m-4 rounded border border-red-200 bg-red-50 p-4 text-sm" data-testid="error-state">
    <p class="font-medium text-red-800" data-testid="error-message">{{ error.message }}</p>
    <ul v-if="error.warnings.length" class="mt-2 list-disc pl-5 text-red-700">
      <li v-for="warning in error.warnings" :key="warning">{{ warning }}</li>
    </ul>
    <button
      v-if="error.traceback"
      type="button"
      class="mt-2 text-xs text-red-700 underline"
      data-testid="error-traceback-toggle"
      @click="showTraceback = !showTraceback"
    >
      {{ showTraceback ? "Hide details" : "Show details" }}
    </button>
    <pre
      v-if="showTraceback"
      class="mt-2 max-h-96 overflow-auto rounded bg-white p-2 font-mono text-xs text-gray-800"
      data-testid="error-traceback"
      >{{ error.traceback }}</pre>
  </div>
</template>
