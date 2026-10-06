<script setup lang="ts">
import { conceptEntry } from "@/report/glossary";
import type { ReportViewKind } from "@/report/query";
import { useReportView } from "@/report/view";

/** The two views of a model next to the inspector: its elements in tables and its differential
 * equations. The words and their tooltips are the entries of the glossary. */
const view = useReportView();

const options: { kind: ReportViewKind; label: string; summary: string | undefined }[] = (
  ["tables", "equations"] as const
).map((kind) => {
  const entry = conceptEntry(kind);
  return { kind, label: entry?.label ?? kind, summary: entry?.summary };
});
</script>

<template>
  <div
    role="tablist"
    class="inline-flex shrink-0 overflow-hidden rounded border border-gray-300"
    data-testid="view-switch"
  >
    <button
      v-for="option in options"
      :key="option.kind"
      v-tooltip.bottom="option.summary"
      type="button"
      role="tab"
      :aria-selected="view.state.value.view === option.kind"
      class="px-2.5 py-0.5 first-letter:uppercase not-first:border-l not-first:border-gray-300 max-md:py-1.5"
      :class="
        view.state.value.view === option.kind ? 'bg-gray-800 text-white' : 'hover:bg-gray-100'
      "
      :data-testid="`view-${option.kind}`"
      @click="view.setView(option.kind)"
    >
      {{ option.label }}
    </button>
  </div>
</template>
