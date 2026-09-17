<script setup lang="ts">
import { DOCS_URL } from "@/report/glossary";
</script>

<template>
  <header
    class="flex h-12 shrink-0 items-center gap-4 border-b border-gray-200 bg-white px-4"
    data-testid="app-bar"
  >
    <RouterLink to="/" class="text-base font-semibold tracking-tight text-gray-900 hover:text-link">
      SBML4Humans
    </RouterLink>
    <div class="flex min-w-0 flex-1 items-center gap-3">
      <slot name="context" />
    </div>
    <div class="flex items-center gap-3">
      <slot name="actions" />
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
    </div>
  </header>
</template>
