<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

import { isPlainClick } from "@/components/help/plainClick";
import { useReportView } from "@/report/view";

/** A link of the help dialog to another entry of the glossary: the breadcrumb, the data type
 * badge, a row of the attributes table and a related entry are all one of these. It is a real
 * anchor with the href of the report with `help=<key>`, so that a reader can middle-click or
 * ctrl-click it into a new tab and so that its target is readable in the status bar; a plain left
 * click keeps the reader in the dialog and shows the entry in place, exactly as a `glossary:`
 * link of a description does, whose click test this shares. */
const props = defineProps<{ helpKey: string }>();

const router = useRouter();
const view = useReportView();
const href = computed(() => router.resolve(view.helpRoute(props.helpKey)).href);

function onClick(event: MouseEvent): void {
  if (!isPlainClick(event)) return;
  event.preventDefault();
  void view.openHelp(props.helpKey);
}
</script>

<template>
  <a :href="href" @click="onClick"><slot /></a>
</template>
