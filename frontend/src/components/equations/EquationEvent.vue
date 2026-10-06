<script setup lang="ts">
import { computed } from "vue";

import type { OdeEvent } from "@/api/types";
import EquationRow from "@/components/equations/EquationRow.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import { attributeLabel } from "@/report/glossary";
import { renderLatex } from "@/report/latex";

/** An event of the differential equations: the event, its trigger, delay and priority, and its
 * assignments as rows. */
const props = defineProps<{ event: OdeEvent; selected: string | null }>();

const parts = computed(() =>
  (
    [
      ["trigger", props.event.trigger],
      ["delay", props.event.delay],
      ["priority", props.event.priority],
    ] as const
  )
    .filter(([, latex]) => latex)
    .map(([field, latex]) => ({
      field,
      label: attributeLabel("Event", field),
      html: renderLatex(latex!, { links: true }),
      latex: latex!,
    })),
);
</script>

<template>
  <div class="mx-4 my-2 rounded border border-gray-200" data-testid="equation-event">
    <div
      class="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-gray-100 bg-gray-50 px-3 py-1 text-sm"
    >
      <ElementLink :pk="event.event" :label="event.label" mark />
      <span v-for="part in parts" :key="part.field" class="flex items-baseline gap-1">
        <span class="text-gray-500">{{ part.label }}</span>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <span v-if="part.html" v-html="part.html" />
        <span v-else class="font-mono text-xs">{{ part.latex }}</span>
      </span>
    </div>
    <EquationRow
      v-for="(equation, k) in event.assignments"
      :key="k"
      :equation="equation"
      :selected="!!selected && equation.variable === selected"
    />
  </div>
</template>
