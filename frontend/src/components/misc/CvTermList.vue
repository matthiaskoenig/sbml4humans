<script setup lang="ts">
import type { CVTerm } from "@/api/types";
import CvTermResourceList from "@/components/misc/CvTermResourceList.vue";

defineProps<{ cvterms: CVTerm[] }>();
</script>

<template>
  <p v-if="cvterms.length === 0" class="text-gray-400">-</p>
  <ul v-else class="flex flex-col gap-2">
    <li v-for="(term, i) in cvterms" :key="i" data-testid="cvterm">
      <p class="font-mono text-xs text-gray-500">{{ term.qualifier }}</p>
      <CvTermResourceList :resources="term.resources" />
    </li>
  </ul>
</template>
