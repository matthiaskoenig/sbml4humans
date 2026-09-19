<script setup lang="ts">
import { computed } from "vue";

import TypeMark from "@/components/misc/TypeMark.vue";
import { useReportIndex } from "@/report/context";
import { conceptEntry } from "@/report/glossary";
import { elementLabel, hasFileId, REPORT_NAME_HINT } from "@/report/label";
import { fileName } from "@/report/text";
import { useReportView } from "@/report/view";

const props = defineProps<{
  pk: string | null | undefined;
  /** The manifest location of the entry of the element, where it is not the one shown: a
   * reference of a comp model may end in another document of the archive. */
  entry?: string | null;
  label?: string | null;
  mark?: boolean;
}>();
const shown = useReportIndex();
const view = useReportView();

/** The index of the entry which holds the element, and its location where it is another one. */
const index = computed(() => shown.value?.entry(props.entry) ?? null);
const across = computed(() =>
  index.value && index.value !== shown.value ? index.value.location : null,
);
const target = computed(() => (props.pk ? index.value?.get(props.pk) : undefined));
const text = computed(() => props.label ?? elementLabel(index.value, props.pk) ?? "-");
const route = computed(() => {
  if (!target.value) return null;
  return across.value && index.value
    ? view.routeFor(target.value.pk, {
        entry: across.value,
        model: index.value.modelIdOf(target.value.pk),
      })
    : view.routeFor(target.value.pk);
});
const acrossHint = computed(() => conceptEntry("targetEntry")?.summary);
/** The link names an element the file gives no id by the name the report gives it, which is
 * set apart from an id; a label the caller passes is what the file writes. */
/** The name cut after every dot, where a name the report gives may wrap in a narrow column. */
const parts = computed(() => text.value.split(/(?<=\.)/));
const reportName = computed(
  () => !props.label && !!target.value && !hasFileId(index.value, props.pk),
);
</script>

<template>
  <RouterLink
    v-if="target && route"
    :to="route"
    class="font-mono text-link hover:underline"
    :class="{ 'inline-flex items-center gap-1': mark, 'flex-wrap': mark && across }"
    :data-pk="target.pk"
    :data-entry="across"
    data-testid="element-link"
    @click.stop
  >
    <TypeMark v-if="mark && target.sbmlType" :type="target.sbmlType" />
    <!-- the name the report gives may break after a dot, between the owner and its part -->
    <span
      v-if="reportName"
      v-tooltip.bottom="REPORT_NAME_HINT"
      class="italic"
      data-testid="report-name"
      ><template v-for="(part, i) in parts" :key="i"><wbr v-if="i > 0" />{{ part }}</template></span
    >
    <span v-else>{{ text }}</span>
    <!-- the document of an element of another entry, which the link opens -->
    <span
      v-if="across"
      v-tooltip.bottom="acrossHint"
      class="font-sans text-xs text-gray-500"
      :class="{ 'ml-1': !mark }"
      data-testid="element-link-entry"
      >{{ fileName(across) }}</span
    >
  </RouterLink>
  <span v-else class="font-mono" :class="{ 'text-gray-400': text === '-' }">{{ text }}</span>
</template>
