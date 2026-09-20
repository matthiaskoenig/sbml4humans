<script setup lang="ts">
import { computed } from "vue";

import type { SbmlElement, ElementType } from "@/api/types";
import HelpButton from "@/components/help/HelpButton.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import ElementTable from "@/components/report/ElementTable.vue";
import { typeKey } from "@/report/glossary";

const props = defineProps<{
  type: ElementType;
  rows: SbmlElement[];
  allRows: SbmlElement[];
  total: number;
  /** The pk of the list of the model which holds the elements of the table, where the list
   * states something of its own and so is an element of the report. */
  list?: string | null;
}>();

const helpKey = computed(() => typeKey(props.type));
</script>

<template>
  <section :id="`section-${type}`" class="scroll-mt-2" :data-testid="`section-${type}`">
    <div class="flex items-center gap-2 px-1 pt-4 pb-2 text-sm font-semibold text-gray-800">
      <!-- the heading names the type and the count alone, so a screen reader announces exactly
      what it shows; the help of the type stands next to it, outside the heading, and is always
      there, unlike the one of a column header, which a header as dense as a table row shows on
      hover, but a heading is not a control and does not carry one -->
      <h2 class="flex items-center gap-1">
        <TypeMark :type="type" size="md" />
        {{ type }}
      </h2>
      <HelpButton v-if="helpKey" :help-key="helpKey" :label="type" />
      <span class="font-mono text-xs font-normal text-gray-500" data-testid="section-count">
        {{ rows.length === total ? total : `${rows.length} / ${total}` }}
      </span>
      <!-- the list the rows are the elements of, where the file says something about it: the
      notes of a `listOfSpecies` are about the table as a whole and belong to no row of it -->
      <span
        v-if="list"
        class="ml-1 min-w-0 truncate text-xs font-normal"
        data-testid="section-list"
      >
        <ElementLink :pk="list" mark />
      </span>
    </div>
    <div class="overflow-hidden rounded border border-gray-200">
      <ElementTable :type="type" :rows="rows" :all-rows="allRows" />
    </div>
  </section>
</template>
