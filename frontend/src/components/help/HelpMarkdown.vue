<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import { isPlainClick } from "@/components/help/plainClick";
import { renderHelpMarkdown } from "@/report/helpMarkdown";
import { useReportView } from "@/report/view";

/** Renders the markdown of one glossary entry's description (`HelpEntry.description`), used by
 * the help dialog for the entry it currently shows. A `glossary:<key>` link of the description
 * becomes a real href of the report so a reader can middle-click or ctrl-click it open in a new
 * tab, but a plain click instead emits `navigate` and never leaves the page: `HelpDialog.vue`
 * (the next task) catches it and shows that entry in the same dialog. */
const props = defineProps<{ markdown: string }>();
const emit = defineEmits<{ navigate: [key: string] }>();

const router = useRouter();
const view = useReportView();

const html = computed(() =>
  renderHelpMarkdown(props.markdown, (key) => router.resolve(view.helpRoute(key)).href),
);

/** A plain left click on a `glossary:` link: `preventDefault()` keeps the browser on the dialog
 * and `navigate` shows the entry in place. Any other click is left alone, so ctrl-click,
 * shift-click and middle-click open the href in a new tab or window the way a reader expects of a
 * real link; `HelpLink.vue`, the links the dialog builds itself, judges a click the same way. */
function onClick(event: MouseEvent): void {
  if (!isPlainClick(event)) return;
  const link = (event.target as Element | null)?.closest("a[data-help-key]");
  const key = link?.getAttribute("data-help-key");
  if (!key) return;
  event.preventDefault();
  emit("navigate", key);
}
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div class="help-markdown" data-testid="help-markdown" @click="onClick" v-html="html" />
</template>

<style scoped>
@reference "@/assets/main.css";

.help-markdown :deep(p) {
  @apply mb-3 leading-relaxed;
}
.help-markdown :deep(p:last-child) {
  @apply mb-0;
}
.help-markdown :deep(code) {
  @apply rounded bg-gray-100 px-1 font-mono text-[0.85em];
}
.help-markdown :deep(a) {
  @apply text-link hover:underline;
}
.help-markdown :deep(ul) {
  @apply mb-3 list-disc pl-5;
}
.help-markdown :deep(li) {
  @apply my-0.5;
}
</style>
