<script setup lang="ts">
import { ref } from "vue";

import type { ApiError } from "@/api/client";
import HelpLabel from "@/components/help/HelpLabel.vue";
import { conceptEntry, conceptKey } from "@/report/glossary";

/** The failure of the validation in the inspector of the document, where the chip of the app bar
 * leads: its message and warnings, and its traceback behind "Show details" where the server sent
 * one (the local server of `sbml4humans.show`), like `ErrorState` of a report which failed. */
defineProps<{ error: ApiError }>();
const concept = conceptEntry("validation");
const showTraceback = ref(false);
</script>

<template>
  <section class="mb-3" data-testid="validation-failure">
    <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
      <HelpLabel :help-key="conceptKey('validation')" :tooltip="concept?.summary">{{
        concept?.label
      }}</HelpLabel>
    </h3>
    <div class="rounded border border-gray-300 bg-gray-50 px-2 py-1.5 text-sm text-gray-700">
      <p data-testid="validation-failure-message">
        The validation failed: <span class="break-words">{{ error.message }}</span>
      </p>
      <ul v-if="error.warnings.length" class="mt-1 list-disc pl-5 text-xs">
        <li v-for="warning in error.warnings" :key="warning">{{ warning }}</li>
      </ul>
      <button
        v-if="error.traceback"
        type="button"
        class="mt-1 text-xs text-gray-600 underline"
        :aria-expanded="showTraceback"
        data-testid="validation-failure-toggle"
        @click="showTraceback = !showTraceback"
      >
        {{ showTraceback ? "Hide details" : "Show details" }}
      </button>
      <pre
        v-if="showTraceback"
        class="mt-1 max-h-96 overflow-auto rounded bg-white p-2 font-mono text-xs text-gray-800"
        data-testid="validation-failure-traceback"
        >{{ error.traceback }}</pre>
    </div>
  </section>
</template>
