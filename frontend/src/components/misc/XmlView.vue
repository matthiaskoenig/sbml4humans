<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

import { type XmlTokenKind, valueParts, xmlLines } from "@/report/xml";

const props = withDefaults(
  defineProps<{ xml: string | null | undefined; emptyMessage?: string; caption?: string }>(),
  { emptyMessage: "No XML available.", caption: undefined },
);
const state = ref<"idle" | "copied" | "failed">("idle");
let reset: ReturnType<typeof setTimeout> | null = null;

const lines = computed(() => (props.xml ? xmlLines(props.xml) : []));

/** The quiet palette: the names of the elements and the values carry the colour, the text of an
 * element is the content and is bold, the punctuation and every other markup recede. */
const KIND_CLASS: Record<XmlTokenKind, string> = {
  punct: "text-gray-400",
  prefix: "text-gray-500",
  name: "text-blue-700",
  attribute: "text-gray-600",
  value: "text-emerald-700",
  text: "font-semibold text-gray-900",
  entity: "text-emerald-700",
  markup: "text-gray-400 italic",
};

/** A wrapped line hangs this many characters beyond the indentation of its line. */
const HANG = 4;

async function copy(): Promise<void> {
  if (!props.xml) return;
  try {
    await navigator.clipboard.writeText(props.xml);
    state.value = "copied";
  } catch {
    state.value = "failed";
  }
  if (reset !== null) clearTimeout(reset);
  reset = setTimeout(() => (state.value = "idle"), 1500);
}

onBeforeUnmount(() => {
  if (reset !== null) clearTimeout(reset);
});
</script>

<template>
  <div class="flex h-full flex-col" data-testid="xml-view">
    <p v-if="!xml" class="text-sm text-gray-400">{{ emptyMessage }}</p>
    <template v-else>
      <div class="mb-1 flex items-center gap-2">
        <!-- the caption says what the xml is when it is not the whole element: the document and
        the model carry their annotation element alone -->
        <p v-if="caption" class="min-w-0 flex-1 text-xs text-gray-500" data-testid="xml-caption">
          {{ caption }}
        </p>
        <button
          type="button"
          class="ml-auto shrink-0 rounded border border-gray-300 bg-white px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-100"
          data-testid="xml-copy"
          @click="copy"
        >
          {{ state === "copied" ? "Copied" : state === "failed" ? "Failed" : "Copy" }}
        </button>
      </div>
      <!-- a line wraps inside the box, at the spaces between attributes and after the separators
      of a url (`<wbr>`, which a selection does not copy), a word longer than the line anywhere;
      its continuation hangs beyond the indentation of the line, which stays text of the line so
      that a selection copies it -->
      <pre
        class="min-h-0 flex-1 overflow-y-auto rounded bg-gray-50 p-3 font-mono text-xs leading-relaxed text-gray-900"
        data-testid="xml-code"
      ><div
          v-for="(line, index) in lines"
          :key="index"
          class="whitespace-pre-wrap wrap-anywhere"
          :style="{
            paddingLeft: `${line.indent + HANG}ch`,
            textIndent: `-${line.indent + HANG}ch`,
          }"
          data-testid="xml-line"
        ><template v-for="(token, t) in line.tokens" :key="t"><span
              v-if="token.kind === 'value'"
              :class="KIND_CLASS.value"
              ><template v-for="(part, p) in valueParts(token.text)" :key="p"
                ><wbr v-if="p > 0" />{{ part }}</template
              ></span
            ><span v-else :class="KIND_CLASS[token.kind]">{{ token.text }}</span></template
          ><br v-if="!line.tokens.length" /></div></pre>
    </template>
  </div>
</template>
