<script setup lang="ts">
import { computed } from "vue";

import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { conceptEntry } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";

/** The counts of the errors and the warnings of the document; a click opens their list, which
 * is the inspector of the document. A valid document shows nothing. */
const props = defineProps<{ index: ReportIndex }>();
const view = useReportView();
const counts = computed(() => props.index.issueCounts);
const tooltip = computed(() => conceptEntry("validation")?.summary);
</script>

<template>
  <!-- "error" and "warning" are the severities of libsbml, the values the glossary lists for
  validationSeverity; a narrow window keeps the counts and leaves the words out -->
  <span
    v-if="counts.error + counts.warning > 0"
    class="flex shrink-0 items-center gap-1"
    data-testid="validation-summary"
  >
    <button
      v-if="counts.error > 0"
      v-tooltip.bottom="tooltip"
      type="button"
      class="flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-xs text-red-700 tabular-nums hover:bg-red-100"
      data-testid="validation-errors"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="error" />{{ counts.error
      }}<span class="max-md:hidden">error{{ counts.error === 1 ? "" : "s" }}</span>
    </button>
    <button
      v-if="counts.warning > 0"
      v-tooltip.bottom="tooltip"
      type="button"
      class="flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-700 tabular-nums hover:bg-amber-100"
      data-testid="validation-warnings"
      @click="view.select(index.document.pk)"
    >
      <SeverityIcon severity="warning" />{{ counts.warning
      }}<span class="max-md:hidden">warning{{ counts.warning === 1 ? "" : "s" }}</span>
    </button>
  </span>
</template>
