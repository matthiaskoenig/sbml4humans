<script setup lang="ts">
import type { CVTerm } from "@/api/types";
import CvTermResourceList from "@/components/misc/CvTermResourceList.vue";

/** The terms which qualify a CV term, indented under it and recursive: a nested term can carry
 * terms of its own (core §6). `autoResolveLimit` is 0 while the element's automatic resolve
 * budget is spent on the terms of the element itself, so a nested resource is shown as the link
 * it is until a "show all" or "resolve all" click resolves it. */
defineProps<{ terms: CVTerm[]; autoResolveLimit: number }>();
</script>

<template>
  <ul class="mt-1 ml-2 flex flex-col gap-1 border-l border-gray-200 pl-2">
    <li v-for="(term, i) in terms" :key="i" data-testid="cvterm-nested">
      <p class="font-mono text-xs text-gray-500">{{ term.qualifier }}</p>
      <CvTermResourceList :resources="term.resources" :auto-resolve-limit="autoResolveLimit" />
      <CvTermNestedList
        v-if="term.nested?.length"
        :terms="term.nested"
        :auto-resolve-limit="autoResolveLimit"
      />
    </li>
  </ul>
</template>
