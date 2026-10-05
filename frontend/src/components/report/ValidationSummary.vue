<script setup lang="ts">
import { computed } from "vue";

import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { conceptEntry } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";

/** The counts of the errors and the warnings of the document; a click opens their list, which
 * is the inspector of the document. A valid document shows nothing, a document libsbml did not
 * check says so, so that the missing counts are not read as a valid document. */
const props = defineProps<{ index: ReportIndex }>();
const view = useReportView();
const counts = computed(() => props.index.issueCounts);
const skipped = computed(() => props.index.validationSkipped !== null);
const tooltip = computed(() => conceptEntry("validation")?.summary);

/** "error" and "warning" are the severities of libsbml, the values the glossary lists for
 * validationSeverity. */
function words(count: number, severity: "error" | "warning"): string {
  return count === 1 ? severity : `${severity}s`;
}
</script>

<template>
  <!-- a narrow window keeps the counts and leaves the words out, the name of a chip keeps both -->
  <span
    v-if="skipped || counts.error + counts.warning > 0"
    class="flex shrink-0 items-center gap-1"
    data-testid="validation-summary"
  >
    <button
      v-if="counts.error > 0"
      v-tooltip.bottom="tooltip"
      type="button"
      class="flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-xs text-red-700 tabular-nums hover:bg-red-100"
      :aria-label="`${counts.error} ${words(counts.error, 'error')}`"
      data-testid="validation-errors"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="error" />{{ counts.error }}
      <span class="max-md:hidden">{{ words(counts.error, "error") }}</span>
    </button>
    <button
      v-if="counts.warning > 0"
      v-tooltip.bottom="tooltip"
      type="button"
      class="flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-700 tabular-nums hover:bg-amber-100"
      :aria-label="`${counts.warning} ${words(counts.warning, 'warning')}`"
      data-testid="validation-warnings"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="warning" />{{ counts.warning }}
      <span class="max-md:hidden">{{ words(counts.warning, "warning") }}</span>
    </button>
    <!-- the words of the chip are its own: no severity of libsbml, the check did not run -->
    <button
      v-if="skipped"
      v-tooltip.bottom="
        'libsbml did not check this document, the inspector of the document says why'
      "
      type="button"
      class="flex items-center gap-1 rounded-full border border-gray-300 bg-gray-50 px-2 py-0.5 text-xs whitespace-nowrap text-gray-700 hover:bg-gray-100"
      aria-label="not validated"
      data-testid="validation-skipped"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="info" /><span class="max-md:hidden">not validated</span>
    </button>
  </span>
</template>
