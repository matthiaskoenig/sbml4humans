<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import logo from "@/assets/logo.png";
import { issueUrl } from "@/feedback";
import { DOCS_URL } from "@/report/glossary";
import { useReportStore } from "@/stores/report";

const route = useRoute();
const store = useReportStore();

/** The report routes show the report of the store, every other page shows none. */
const feedbackUrl = computed(() =>
  issueUrl({
    fullPath: route.fullPath,
    path: route.path,
    source: route.name === "example" || route.name === "report" ? store.source : null,
  }),
);
</script>

<template>
  <header
    class="flex h-12 shrink-0 items-center gap-4 border-b border-gray-200 bg-white px-4"
    data-testid="app-bar"
  >
    <RouterLink
      to="/"
      class="flex shrink-0 items-center gap-2 text-base font-semibold tracking-tight text-gray-900 hover:text-link"
    >
      <img :src="logo" alt="The logo of SBML4Humans" class="size-6" data-testid="app-logo" />
      SBML4Humans
    </RouterLink>
    <slot name="search" />
    <div class="flex min-w-0 flex-1 items-center gap-3">
      <slot name="context" />
    </div>
    <div class="flex items-center gap-3">
      <a
        :href="DOCS_URL"
        target="_blank"
        rel="noopener"
        class="text-sm text-gray-600 hover:text-link"
        data-testid="app-bar-docs"
        >Documentation</a
      >
      <RouterLink :to="{ name: 'examples' }" class="text-sm text-gray-600 hover:text-link"
        >Examples</RouterLink
      >
      <!-- feedback is an issue of the repository, which opens with the build, the page and the
      model already written, so that a reader only has to say what they saw -->
      <a
        v-tooltip.bottom="'Open an issue on GitHub'"
        :href="feedbackUrl"
        target="_blank"
        rel="noopener"
        class="text-sm text-gray-600 hover:text-link"
        data-testid="app-bar-feedback"
        >Feedback</a
      >
    </div>
  </header>
</template>
