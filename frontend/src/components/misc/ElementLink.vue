<script setup lang="ts">
import { computed } from "vue";

import TypeMark from "@/components/misc/TypeMark.vue";
import { useReportIndex } from "@/report/context";
import { pkKey } from "@/report/pk";
import { useReportView } from "@/report/view";

const props = defineProps<{
  pk: string | null | undefined;
  label?: string | null;
  mark?: boolean;
}>();
const index = useReportIndex();
const view = useReportView();

const target = computed(() => (props.pk ? index.value?.get(props.pk) : undefined));
// an element without an id, such as a rule of a Level 2 model or a species reference, is named
// by the key of its primary key, which is its meta id or the name its parent gives it:
// `R1.reactant.S1` instead of `model/SpeciesReference:R1.reactant.S1`
const text = computed(() => props.label ?? target.value?.id ?? pkKey(props.pk) ?? "-");
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
    <span>{{ text }}</span>
  </RouterLink>
  <span v-else class="font-mono" :class="{ 'text-gray-400': text === '-' }">{{ text }}</span>
</template>
