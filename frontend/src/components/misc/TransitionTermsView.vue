<script setup lang="ts">
import MathView from "@/components/misc/MathView.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { OTHERWISE, type TransitionTerm } from "@/report/transitionTerms";

/** The transition table of a transition on the one line of its row, read as the piecewise
 * function it is: `level if condition` for every function term in the order of the file, the
 * first of which whose condition holds decides, and `level otherwise` for the default term. The
 * inspector shows the same rows as a table, with a link to every term. */
defineProps<{ terms: TransitionTerm[] }>();

const IF = " if ";
const ELSE = ` ${OTHERWISE}`;
// a condition may hold a comma of its own, the arguments of a function, so a semicolon separates
const NEXT = "; ";
</script>

<template>
  <ValueText v-if="!terms.length" :value="null" />
  <!-- the separators are text of their own, so that the cell reads as the rule it is -->
  <span v-else data-testid="transition-terms">
    <template v-for="(term, i) in terms" :key="term.pk">
      <span v-if="i > 0" class="text-gray-500">{{ NEXT }}</span>
      <span data-testid="result-level"><ValueText :value="term.resultLevel" /></span>
      <span v-if="term.isDefault" class="text-gray-500 italic">{{ ELSE }}</span>
      <template v-else>
        <span class="text-gray-500">{{ IF }}</span>
        <MathView :math="term.math" />
      </template>
    </template>
  </span>
</template>
