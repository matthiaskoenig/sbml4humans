<script setup lang="ts">
import type { ElementType, SbmlElement } from "@/api/types";
import ElementSection from "@/components/report/ElementSection.vue";

/** The elements of one type of the current model: the ones the search leaves and all of them. */
export interface TableSection {
  type: ElementType;
  rows: SbmlElement[];
  all: SbmlElement[];
  total: number;
  list: string | null;
}

defineProps<{ sections: TableSection[]; emptyMessage: string }>();
</script>

<template>
  <!-- the tables of the report in the one scroll they share: the second pane of the split of a
  wide window, the whole page of a narrow one -->
  <div class="h-full overflow-y-auto px-4 pb-8" data-testid="tables">
    <p
      v-if="sections.length === 0"
      class="p-8 text-center text-sm text-gray-500"
      data-testid="no-matches"
    >
      {{ emptyMessage }}
    </p>
    <ElementSection
      v-for="section in sections"
      :key="section.type"
      :type="section.type"
      :rows="section.rows"
      :all-rows="section.all"
      :total="section.total"
      :list="section.list"
    />
  </div>
</template>
