<script setup lang="ts">
import { computed } from "vue";

import TypeMark from "@/components/misc/TypeMark.vue";
import { useReportIndex } from "@/report/context";
import { elementLabel, hasFileId, REPORT_NAME_HINT } from "@/report/label";
import { useReportView } from "@/report/view";

const props = defineProps<{
  pk: string | null | undefined;
  label?: string | null;
  mark?: boolean;
}>();
const index = useReportIndex();
const view = useReportView();

const target = computed(() => (props.pk ? index.value?.get(props.pk) : undefined));
const text = computed(() => props.label ?? elementLabel(index.value, props.pk) ?? "-");
/** The link names an element the file gives no id by the name the report gives it, which is
 * set apart from an id; a label the caller passes is what the file writes. */
const reportName = computed(
  () => !props.label && !!target.value && !hasFileId(index.value, props.pk),
);
</script>

<template>
  <RouterLink
    v-if="target"
    :to="view.routeFor(target.pk)"
    class="inline-flex items-center gap-1 font-mono text-link hover:underline"
    :data-pk="target.pk"
    data-testid="element-link"
    @click.stop
  >
    <TypeMark v-if="mark && target.sbmlType" :type="target.sbmlType" />
    <span
      v-if="reportName"
      v-tooltip.bottom="REPORT_NAME_HINT"
      class="italic"
      data-testid="report-name"
      >{{ text }}</span
    >
    <span v-else>{{ text }}</span>
  </RouterLink>
  <span v-else class="font-mono" :class="{ 'text-gray-400': text === '-' }">{{ text }}</span>
</template>
