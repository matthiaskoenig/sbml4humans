import { defineStore } from "pinia";
import { ref } from "vue";

import { type ApiError, getExamples, toApiError } from "@/api/client";
import type { ExampleMetaData } from "@/api/types";

export const useExamplesStore = defineStore("examples", () => {
  const examples = ref<ExampleMetaData[]>([]);
  const loading = ref(false);
  const error = ref<ApiError | null>(null);

  /** Load the examples once. */
  async function loadExamples(): Promise<void> {
    if (examples.value.length > 0 || loading.value) return;
    loading.value = true;
    error.value = null;
    try {
      examples.value = await getExamples();
    } catch (caught) {
      error.value = toApiError(caught);
    } finally {
      loading.value = false;
    }
  }

  return { examples, loading, error, loadExamples };
});
