<script setup lang="ts">
import { CircleOffIcon, LoaderCircleIcon } from "@lucide/vue";
import { computed } from "vue";

import type { ApiError } from "@/api/client";
import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { useValidationIndex } from "@/report/context";
import { conceptEntry } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import type { EntrySkip } from "@/report/validationIndex";
import { useReportView } from "@/report/view";
import type { ValidationState } from "@/stores/report";

/** The counts of the errors and the warnings of the document; a click opens their list, which
 * is the inspector of the document. A valid document shows nothing, a document libsbml did not
 * check says so, so that the missing counts are not read as a valid document. The validation is
 * answered after the report: while it runs a quiet chip says so, and a validation which failed
 * says that it failed, with the message of the failure as its tooltip. */
defineProps<{
  index: ReportIndex;
  state: ValidationState | null;
  error: ApiError | null;
}>();
const view = useReportView();
const validation = useValidationIndex();
const counts = computed(() => validation.value?.issueCounts ?? { error: 0, warning: 0, info: 0 });
const skipped = computed(() => validation.value?.skipped ?? null);
const tooltip = computed(() => conceptEntry("validation")?.summary);

/** Why libsbml did not check the document, in the words of the chip: no severity of libsbml, the
 * check did not run. The inspector of the document says it at length. A busy server is asked again
 * by a reload, unless the source is a file or pasted content, which a reload loses. */
const SKIPPED: Record<Exclude<EntrySkip, "busy">, string> = {
  expandedSize:
    "libsbml did not check this document: its comp submodels expand it beyond the size which is checked",
  timeout: "libsbml did not check this document: the check did not end in time",
  memory: "libsbml did not check this document: the check needed more memory than it may use",
  unanswered: "libsbml did not check this document: the validation answered nothing for it",
};
const skippedText = computed(() => {
  const reason = skipped.value;
  if (reason === null) return undefined;
  if (reason !== "busy") return SKIPPED[reason];
  return validation.value?.reloadable === false
    ? "libsbml did not check this document: the server was busy, load it again later to try again"
    : "libsbml did not check this document: the server was busy, reload the report later to try again";
});

/** "error" and "warning" are the severities of libsbml, the values the glossary lists for
 * validationSeverity. */
function words(count: number, severity: "error" | "warning"): string {
  return count === 1 ? severity : `${severity}s`;
}
</script>

<template>
  <!-- a narrow window keeps the counts and leaves the words out, the name of a chip keeps both -->
  <span
    v-if="state === 'pending'"
    v-tooltip.bottom="
      'libsbml checks the document, its errors and warnings appear here when it is done'
    "
    class="flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs whitespace-nowrap text-gray-500"
    role="status"
    aria-label="validating"
    data-testid="validation-pending"
  >
    <LoaderCircleIcon class="size-3.5 animate-spin" /><span class="max-md:hidden">validating</span>
  </span>
  <span
    v-else-if="state === 'failed'"
    v-tooltip.bottom="error?.message"
    tabindex="0"
    class="flex shrink-0 items-center gap-1 rounded-full border border-gray-300 bg-gray-50 px-2 py-0.5 text-xs whitespace-nowrap text-gray-700"
    aria-label="validation failed"
    data-testid="validation-failed"
  >
    <CircleOffIcon class="size-3.5 text-gray-500" /><span class="max-md:hidden"
      >validation failed</span
    >
  </span>
  <span
    v-else-if="skipped || counts.error + counts.warning > 0"
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
    <button
      v-if="skipped"
      v-tooltip.bottom="skippedText"
      type="button"
      class="flex items-center gap-1 rounded-full border border-gray-300 bg-gray-50 px-2 py-0.5 text-xs whitespace-nowrap text-gray-700 hover:bg-gray-100"
      aria-label="not validated"
      :data-reason="skipped"
      data-testid="validation-skipped"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="info" /><span class="max-md:hidden">not validated</span>
    </button>
  </span>
</template>
