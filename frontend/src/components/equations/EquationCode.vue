<script setup lang="ts">
import { CheckIcon, CopyIcon, DownloadIcon, ExternalLinkIcon } from "@lucide/vue";
import { onBeforeUnmount, ref, watch } from "vue";

import { type ApiError, type OdeFormat, toApiError } from "@/api/client";
import HelpButton from "@/components/help/HelpButton.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import { conceptEntry, conceptKey } from "@/report/glossary";
import { highlight } from "@/report/highlight";
import { type OdeCode, useReportStore } from "@/stores/report";

/** The code of the differential equations in a format of sbmlode, the ODE system alone: the
 * backend writes it from the source of the report, which the store sends again once per format
 * and entry. The code is highlighted by Shiki (its HTML escapes the code), a code too long for it
 * is shown as text. Copy and download take the code shown; the help explains the code and links
 * the formats of sbmlode, which writes custom exports. A failure, the code of a model with an
 * unsupported construct for example, is shown in place of the code. */
const props = defineProps<{ format: OdeFormat; location: string }>();
const store = useReportStore();
const entry = conceptEntry("odeDownload");
const helpKey = conceptKey("odeDownload");

/** The page of the formats of sbmlode, where its custom exports are described. */
const SBMLODE_FORMATS_URL = "https://matthiaskoenig.github.io/sbmlode/formats/";

const code = ref<OdeCode | null>(null);
const html = ref<string | null>(null);
const error = ref<ApiError | null>(null);
const copied = ref(false);
let copiedTimer: ReturnType<typeof setTimeout> | undefined;

watch(
  () => [props.format, props.location] as const,
  async ([format, location], _previous, onCleanup) => {
    let stale = false;
    onCleanup(() => {
      stale = true;
    });
    code.value = null;
    html.value = null;
    error.value = null;
    try {
      const fetched = await store.odeCode(format, location);
      if (stale) return;
      code.value = fetched;
      const highlighted = await highlight(fetched.text, format).catch(() => null);
      if (!stale) html.value = highlighted;
    } catch (caught) {
      if (!stale) error.value = toApiError(caught);
    }
  },
  { immediate: true },
);

async function copy(): Promise<void> {
  if (!code.value) return;
  await navigator.clipboard.writeText(code.value.text);
  copied.value = true;
  clearTimeout(copiedTimer);
  copiedTimer = setTimeout(() => (copied.value = false), 1200);
}

function download(): void {
  if (!code.value) return;
  const url = URL.createObjectURL(new Blob([code.value.text], { type: "text/plain" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = code.value.filename;
  link.click();
  // the browser reads the file once the click is handled
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

onBeforeUnmount(() => clearTimeout(copiedTimer));
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col" data-testid="equations-code">
    <div
      class="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-gray-200 bg-gray-50 px-4 py-1.5 text-xs"
    >
      <span class="font-mono text-gray-700" data-testid="equations-code-filename">{{
        code?.filename ?? ""
      }}</span>
      <span v-tooltip.bottom="entry?.summary" class="inline-flex">
        <HelpButton v-if="helpKey" :help-key="helpKey" :label="entry?.label ?? ''" size="sm" />
      </span>
      <span class="ml-auto flex items-center gap-2">
        <a
          :href="SBMLODE_FORMATS_URL"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1 text-link hover:underline"
          data-testid="equations-code-sbmlode"
          >Custom exports with sbmlode<ExternalLinkIcon class="size-3" aria-hidden="true"
        /></a>
        <button
          type="button"
          class="inline-flex items-center gap-1 rounded border border-gray-300 bg-white px-2 py-0.5 hover:bg-gray-100 disabled:opacity-50"
          :disabled="!code"
          data-testid="equations-code-copy"
          @click="copy"
        >
          <component :is="copied ? CheckIcon : CopyIcon" class="size-3" aria-hidden="true" />
          {{ copied ? "Copied" : "Copy" }}
        </button>
        <button
          type="button"
          class="inline-flex items-center gap-1 rounded border border-gray-300 bg-white px-2 py-0.5 hover:bg-gray-100 disabled:opacity-50"
          :disabled="!code"
          data-testid="equations-code-download"
          @click="download"
        >
          <DownloadIcon class="size-3" aria-hidden="true" />
          Download
        </button>
      </span>
    </div>
    <div v-if="error" data-testid="equations-code-error">
      <ErrorState :error="error" />
    </div>
    <p
      v-else-if="!code"
      class="px-4 py-3 text-xs text-gray-500"
      data-testid="equations-code-loading"
    >
      Loading the code…
    </p>
    <div
      v-else-if="html"
      class="min-h-0 flex-1 overflow-auto [&_pre]:min-w-max [&_pre]:px-4 [&_pre]:py-3 [&_pre]:text-xs [&_pre]:leading-5"
      data-testid="equations-code-text"
    >
      <!-- eslint-disable-next-line vue/no-v-html -- the HTML of Shiki, which escapes the code -->
      <div v-html="html" />
    </div>
    <pre
      v-else
      class="min-h-0 flex-1 overflow-auto px-4 py-3 font-mono text-xs leading-5 text-gray-800"
      data-testid="equations-code-text"
      >{{ code.text }}</pre>
  </div>
</template>
