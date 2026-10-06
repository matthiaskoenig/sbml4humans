<script setup lang="ts">
import { computed } from "vue";

import EquationRow from "@/components/equations/EquationRow.vue";
import { useReportIndex } from "@/report/context";
import { conceptEntry, type GlossaryEntry } from "@/report/glossary";
import type { OdeSection } from "@/report/index";
import { useReportView } from "@/report/view";

/** The equations of an element in the inspector: the ODE of a state, the rate of a reaction, an
 * assignment, an initial value, with the heading of their section and a link to the view of the
 * equations, which opens with the element selected. */
const props = defineProps<{ pk: string }>();
const index = useReportIndex();
const view = useReportView();

const CONCEPTS: Record<OdeSection, string> = {
  odes: "odeSystem",
  reactions: "reactionRates",
  assignments: "odeAssignments",
  functions: "odeFunctions",
  initial: "odeInitial",
  events: "odeEvents",
};

const equations = computed(() => index.value?.equationsOf(props.pk) ?? []);
const entry: GlossaryEntry | undefined = conceptEntry("equations");

function sectionLabel(section: OdeSection): string {
  return conceptEntry(CONCEPTS[section])?.label ?? section;
}

function show(): void {
  void view.setView("equations");
}

/** A symbol of an equation selects its element, as in the view of the equations. */
function onClick(event: MouseEvent): void {
  const pk = (event.target as HTMLElement | null)?.closest<HTMLElement>("[data-pk]")?.dataset.pk;
  if (pk && index.value?.has(pk)) void view.select(pk);
}
</script>

<template>
  <section
    v-if="equations.length"
    class="flex flex-col gap-1"
    data-testid="equation-block"
    @click="onClick"
  >
    <div class="flex items-baseline gap-2 text-xs font-semibold text-gray-600">
      <span class="first-letter:uppercase">{{ entry?.label }}</span>
      <button
        v-if="view.state.value.view !== 'equations'"
        type="button"
        class="font-normal text-link hover:underline"
        data-testid="equation-block-show"
        @click="show"
      >
        show in {{ entry?.label }}
      </button>
    </div>
    <div
      v-for="({ section, equation }, k) in equations"
      :key="k"
      class="rounded border border-gray-200 bg-white"
    >
      <div class="px-2 pt-1 text-xs text-gray-500 first-letter:uppercase">
        {{ sectionLabel(section) }}
      </div>
      <EquationRow :equation="equation" />
    </div>
  </section>
</template>
