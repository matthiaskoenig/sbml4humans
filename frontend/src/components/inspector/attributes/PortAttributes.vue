<script setup lang="ts">
import type { Port } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

const props = defineProps<{ element: Port }>();
const index = useReportIndex();

/** The one port edge of the port; ports reference exactly one element. */
const target = () =>
  index.value?.references(props.element.pk).find((edge) => edge.kind === "port")?.target ?? null;
</script>

<template>
  <AttributeRow label="port ref"><ValueText :value="element.portRef" mono /></AttributeRow>
  <AttributeRow label="id ref">
    <ElementLink v-if="element.idRef" :pk="target()" :label="element.idRef" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="unit ref">
    <ElementLink v-if="element.unitRef" :pk="target()" :label="element.unitRef" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
  <AttributeRow label="meta id ref">
    <ElementLink v-if="element.metaIdRef" :pk="target()" :label="element.metaIdRef" />
    <span v-else class="text-gray-400">-</span>
  </AttributeRow>
</template>
