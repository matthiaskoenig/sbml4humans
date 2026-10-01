<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import AppBar from "@/components/layout/AppBar.vue";
import AppFooter from "@/components/layout/AppFooter.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import { useExamplesStore } from "@/stores/examples";

const store = useExamplesStore();
const filter = ref("");

onMounted(() => void store.loadExamples());

function stripHtml(html: string): string {
  return html
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const examples = computed(() => {
  const query = filter.value.trim().toLowerCase();
  return store.examples
    .map((example) => ({
      ...example,
      text: example.description ? stripHtml(example.description) : "",
    }))
    .filter(
      (example) =>
        !query ||
        example.id.toLowerCase().includes(query) ||
        (example.name ?? "").toLowerCase().includes(query) ||
        example.text.toLowerCase().includes(query),
    );
});
</script>

<template>
  <AppBar />
  <main class="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6" data-testid="examples-page">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <h1 class="text-2xl font-semibold tracking-tight">Examples</h1>
      <input
        v-model="filter"
        type="search"
        placeholder="Filter examples"
        class="w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-link focus:outline-none sm:w-64"
        data-testid="examples-filter"
      />
    </div>
    <LoadingState v-if="store.loading" message="Loading the examples" />
    <ErrorState v-else-if="store.error" :error="store.error" />
    <ul v-else class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="examples-grid">
      <li v-for="example in examples" :key="example.id" class="min-w-0">
        <RouterLink
          :to="{ name: 'example', params: { id: example.id } }"
          class="flex h-full flex-col gap-1 rounded-lg border border-gray-200 p-3 hover:border-gray-400 hover:bg-gray-50"
          data-testid="example-card"
        >
          <!-- the id of a written example names its file behind it, and it wraps at the space
          between the two instead of being cut off -->
          <span class="font-mono text-sm font-medium break-words" data-testid="example-id">{{
            example.id
          }}</span>
          <span v-if="example.name" class="truncate text-sm text-gray-800">{{ example.name }}</span>
          <span v-if="example.text" class="line-clamp-2 text-xs break-words text-gray-500">{{
            example.text
          }}</span>
          <span v-if="example.packages.length" class="mt-auto flex flex-wrap gap-1 pt-1">
            <span
              v-for="pkg in example.packages"
              :key="pkg"
              class="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700"
              >{{ pkg }}</span
            >
          </span>
        </RouterLink>
      </li>
    </ul>
    <AppFooter />
  </main>
</template>
