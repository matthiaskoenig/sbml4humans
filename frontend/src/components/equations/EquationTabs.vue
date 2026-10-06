<script setup lang="ts">
import { nextTick, ref } from "vue";

import type { OdeFormat } from "@/api/client";
import { tabId } from "@/components/equations/tabId";

/** The tabs of the equations: the math, typeset by KaTeX, and the code of each format of
 * sbmlode. `null` is the math. The arrow keys, Home and End move between the tabs and select the
 * tab they move to, as a tablist of WAI-ARIA does; every tab controls the panel `panel`, the
 * element of the view which shows the math or the code, whose label is the selected tab
 * (`tabId`). */
const props = defineProps<{ code: OdeFormat | null; panel: string }>();
const emit = defineEmits<{ select: [code: OdeFormat | null] }>();

/** The tabs in their order, the formats by the name of their language or markup. */
const TABS: { code: OdeFormat | null; name: string; testid: string }[] = [
  { code: null, name: "Math", testid: "equations-tab-math" },
  { code: "python", name: "Python", testid: "equations-tab-python" },
  { code: "julia", name: "Julia", testid: "equations-tab-julia" },
  { code: "r", name: "R", testid: "equations-tab-r" },
  { code: "latex", name: "LaTeX", testid: "equations-tab-latex" },
  { code: "typst", name: "Typst", testid: "equations-tab-typst" },
  { code: "markdown", name: "Markdown", testid: "equations-tab-markdown" },
];

const buttons = ref<(HTMLButtonElement | null)[]>([]);

async function onKeydown(event: KeyboardEvent, index: number): Promise<void> {
  const last = TABS.length - 1;
  const next = {
    ArrowRight: index === last ? 0 : index + 1,
    ArrowLeft: index === 0 ? last : index - 1,
    Home: 0,
    End: last,
  }[event.key];
  if (next === undefined) return;
  event.preventDefault();
  emit("select", TABS[next]!.code);
  await nextTick();
  buttons.value[next]?.focus();
}
</script>

<template>
  <div
    class="flex flex-wrap items-center text-xs"
    role="tablist"
    aria-label="Equations"
    data-testid="equations-tabs"
  >
    <template v-for="(tab, k) in TABS" :key="tab.testid">
      <span v-if="k === 1" class="mx-1 h-4 w-px bg-gray-300" aria-hidden="true" />
      <button
        :id="tabId(tab.code)"
        :ref="(element) => (buttons[k] = element as HTMLButtonElement | null)"
        type="button"
        role="tab"
        :aria-controls="panel"
        class="border-b-2 px-2 py-1 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-link"
        :class="
          props.code === tab.code
            ? 'border-link font-semibold text-link'
            : 'border-transparent text-gray-600'
        "
        :aria-selected="props.code === tab.code"
        :tabindex="props.code === tab.code ? 0 : -1"
        :data-testid="tab.testid"
        @click="emit('select', tab.code)"
        @keydown="onKeydown($event, k)"
      >
        {{ tab.name }}
      </button>
    </template>
  </div>
</template>
