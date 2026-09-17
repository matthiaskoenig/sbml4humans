<script setup lang="ts">
import { computed } from "vue";

import { MAX_AUTO_RESOLVES } from "@/api/annotations";
import type { CVTerm } from "@/api/types";
import CvTermResourceList from "@/components/misc/CvTermResourceList.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { LIST_LIMIT, useLimitedList } from "@/report/limitedList";

const props = defineProps<{ cvterms: CVTerm[] }>();

const {
  shown: shownTerms,
  hiddenCount: hiddenTermsCount,
  showAll: showAllTerms,
} = useLimitedList(() => props.cvterms);

/** How many of the resources of each of the first LIST_LIMIT terms (the terms shown before any
 * "show all" click) resolve automatically, in term order, until MAX_AUTO_RESOLVES is spent. A
 * term revealed only by the terms "show all" is a user action and is not part of this budget,
 * so it always gets Infinity (every resource it shows by default resolves). */
const autoResolveLimits = computed<number[]>(() => {
  let budget = MAX_AUTO_RESOLVES;
  return props.cvterms.slice(0, LIST_LIMIT).map((term) => {
    const shownResourceCount = Math.min(LIST_LIMIT, term.resources.length);
    const granted = Math.max(0, Math.min(shownResourceCount, budget));
    budget -= granted;
    return granted;
  });
});

function autoResolveLimit(index: number): number {
  return autoResolveLimits.value[index] ?? Infinity;
}
</script>

<template>
  <p v-if="cvterms.length === 0" class="text-gray-400">-</p>
  <template v-else>
    <ul class="flex flex-col gap-2">
      <li v-for="(term, i) in shownTerms" :key="i" data-testid="cvterm">
        <p class="font-mono text-xs text-gray-500">{{ term.qualifier }}</p>
        <CvTermResourceList :resources="term.resources" :auto-resolve-limit="autoResolveLimit(i)" />
      </li>
    </ul>
    <ShowAllButton
      v-if="hiddenTermsCount > 0"
      :count="hiddenTermsCount"
      class="mt-1"
      @click="showAllTerms"
    />
  </template>
</template>
