<script setup lang="ts">
import { computed } from "vue";
import { conceptEntry } from "@/report/glossary";
import type { ReportViewKind } from "@/report/query";
import { useReportView } from "@/report/view";

/** Views share the report selection and its inspector. */
const props = withDefaults(defineProps<{ hasEquations?: boolean }>(), { hasEquations: true });
const view = useReportView();

const options = computed(() =>
  (["tables", "network", ...(props.hasEquations ? ["equations"] : [])] as ReportViewKind[]).map(
    (kind) => {
      const entry = conceptEntry(kind);
      return { kind, label: entry?.label ?? kind, summary: entry?.summary };
    },
  ),
);
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
