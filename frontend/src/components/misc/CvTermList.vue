<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

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

/** Set by a click on "resolve all": every shown resource resolves. */
const resolveAll = ref(false);
/** The indexes of the terms whose own "show all" was clicked: such a term resolves every
 * resource it shows. */
const expandedTerms = reactive(new Set<number>());
// both clicks are user actions for the terms of one element, so the budget applies again to the
// terms of another element
watch(
  () => props.cvterms,
  () => {
    resolveAll.value = false;
    expandedTerms.clear();
  },
);

function autoResolveLimit(index: number): number {
  if (resolveAll.value || expandedTerms.has(index)) return Infinity;
  return autoResolveLimits.value[index] ?? Infinity;
}

/** The number of shown resources the budget leaves unresolved. */
const unresolvedCount = computed(() =>
  shownTerms.value.reduce(
    (count, term, index) =>
      count + Math.max(0, Math.min(LIST_LIMIT, term.resources.length) - autoResolveLimit(index)),
    0,
  ),
);
</script>

<template>
  <p v-if="cvterms.length === 0" class="text-gray-400">-</p>
  <template v-else>
    <ul class="flex flex-col gap-2">
      <li v-for="(term, i) in shownTerms" :key="i" data-testid="cvterm">
        <p class="font-mono text-xs text-gray-500">{{ term.qualifier }}</p>
        <CvTermResourceList
          :resources="term.resources"
          :auto-resolve-limit="autoResolveLimit(i)"
          @show-all="expandedTerms.add(i)"
        />
      </li>
    </ul>
    <div v-if="hiddenTermsCount > 0 || unresolvedCount > 0" class="mt-1 flex gap-3">
      <ShowAllButton v-if="hiddenTermsCount > 0" :count="hiddenTermsCount" @click="showAllTerms" />
      <ShowAllButton
        v-if="unresolvedCount > 0"
        label="resolve all"
        :count="unresolvedCount"
        @click="resolveAll = true"
      />
    </div>
  </template>
</template>
