<script setup lang="ts">
import { ref } from "vue";

import type { ApiError } from "@/api/client";
import { type OdeFormat, toApiError } from "@/api/client";
import { conceptEntry, conceptKey } from "@/report/glossary";
import { useReportStore } from "@/stores/report";
import HelpButton from "@/components/help/HelpButton.vue";

/** The downloads of the differential equations in the formats of sbmlode. The backend writes the
 * file from the source of the report, which the store sends again; a failure, a model with an
 * unsupported construct written as code for example, is shown next to the buttons. */
const props = defineProps<{ location: string }>();
const store = useReportStore();
const entry = conceptEntry("odeDownload");
const helpKey = conceptKey("odeDownload");

/** The formats by the name of their language or markup. */
const FORMATS: { format: OdeFormat; name: string }[] = [
  { format: "python", name: "Python" },
  { format: "julia", name: "Julia" },
  { format: "r", name: "R" },
  { format: "latex", name: "LaTeX" },
  { format: "typst", name: "Typst" },
  { format: "markdown", name: "Markdown" },
];

const busy = ref<OdeFormat | null>(null);
const error = ref<ApiError | null>(null);

async function download(format: OdeFormat): Promise<void> {
  busy.value = format;
  error.value = null;
  try {
    const file = await store.downloadOde(format, props.location);
    const url = URL.createObjectURL(file.blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = file.filename;
    link.click();
    // the browser reads the file once the click is handled
    setTimeout(() => URL.revokeObjectURL(url), 0);
  } catch (caught) {
    error.value = toApiError(caught);
  } finally {
    busy.value = null;
  }
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-1.5 text-xs" data-testid="ode-download">
    <span v-tooltip.bottom="entry?.summary" class="text-gray-500 first-letter:uppercase">{{
      entry?.label ?? "download"
    }}</span>
    <HelpButton v-if="helpKey" :help-key="helpKey" :label="entry?.label ?? 'download'" size="sm" />
    <button
      v-for="{ format, name } in FORMATS"
      :key="format"
      type="button"
      class="rounded border border-gray-300 px-2 py-0.5 hover:bg-gray-50 disabled:opacity-50"
      :disabled="busy !== null"
      :data-testid="`ode-download-${format}`"
      @click="download(format)"
    >
      {{ name }}
    </button>
    <span
      v-if="error"
      v-tooltip.bottom="error.message"
      class="max-w-80 truncate text-red-700"
      data-testid="ode-download-error"
      >{{ error.message }}</span
    >
  </div>
</template>
