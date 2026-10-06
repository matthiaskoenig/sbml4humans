<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";

import { ApiError } from "@/api/client";
import type { OdeEquation } from "@/api/types";
import EquationEvent from "@/components/equations/EquationEvent.vue";
import EquationRow from "@/components/equations/EquationRow.vue";
import EquationSection from "@/components/equations/EquationSection.vue";
import OdeDownload from "@/components/equations/OdeDownload.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import HelpButton from "@/components/help/HelpButton.vue";
import { conceptEntry, conceptKey } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import { elementLabel } from "@/report/label";
import { useReportView } from "@/report/view";

/** The differential equations of the model of the document, the view next to the tables: the
 * constructs the system leaves out first, then the ODE system, the reaction rates, the
 * assignment rules, the function definitions, the initial values and the events, a section
 * without an equation left out. A click on a symbol selects its element, the symbols of the
 * selected element are marked in every equation and the row of its own equation is marked. */
const props = defineProps<{ index: ReportIndex; location: string }>();
const view = useReportView();

const system = computed(() => props.index.odeSystem);
const failure = computed(() =>
  props.index.odeError === null ? null : new ApiError(props.index.odeError),
);
const selected = computed(() => view.state.value.pk);
const modelId = computed(() => props.index.mainModel?.id ?? null);
const equations = conceptEntry("equations");
const equationsKey = conceptKey("equations");
const unsupported = conceptEntry("odeUnsupported");
const unsupportedKey = conceptKey("odeUnsupported");

const SECTIONS = [
  ["odes", "odeSystem"],
  ["reactions", "reactionRates"],
  ["assignments", "odeAssignments"],
  ["functions", "odeFunctions"],
  ["initial", "odeInitial"],
] as const;

const sections = computed(() =>
  SECTIONS.map(([field, concept]) => ({
    field,
    concept,
    equations: (system.value?.[field] ?? []) as OdeEquation[],
  }))
    .map((section) => ({
      ...section,
      mixed: new Set(section.equations.map((equation) => equation.origin)).size > 1,
    }))
    .filter((section) => section.equations.length > 0),
);

/** The mark of the symbols of the selected element: a rule of a stylesheet of this view, so that
 * a row which renders later is marked as well. A pk is a string of the report, quoted with
 * `CSS.escape`. */
const markStyle = computed(() => {
  const pk = selected.value;
  if (!pk || typeof CSS === "undefined") return "";
  return `[data-testid="equations-view"] .katex [data-pk="${CSS.escape(pk)}"] { background-color: var(--color-selected); border-radius: 2px; }`;
});

function onClick(event: MouseEvent): void {
  const target = (event.target as HTMLElement | null)?.closest<HTMLElement>("[data-pk]");
  const pk = target?.dataset.pk;
  if (pk && props.index.has(pk)) void view.select(pk);
}

/** The name of the element of a symbol as its tooltip, set when the pointer reaches it. */
function onOver(event: MouseEvent): void {
  const target = (event.target as HTMLElement | null)?.closest<HTMLElement>("[data-pk]");
  if (!target || target.title) return;
  const pk = target.dataset.pk;
  if (pk && props.index.has(pk)) target.title = elementLabel(props.index, pk) ?? pk;
}

/** A view which opens with a selected element, from "show in equations" of the inspector, shows
 * the equation of that element. */
const root = ref<HTMLElement | null>(null);
onMounted(async () => {
  const pk = selected.value;
  if (!pk || !root.value) return;
  await nextTick();
  const row = root.value.querySelector(`[data-equation-of="${CSS.escape(pk)}"]`);
  row?.scrollIntoView({ block: "center" });
});
</script>

<template>
  <div
    ref="root"
    class="flex min-h-0 flex-1 flex-col overflow-y-auto"
    data-testid="equations-view"
    @click="onClick"
    @mouseover="onOver"
  >
    <component :is="'style'" v-if="markStyle">{{ markStyle }}</component>
    <div
      class="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-gray-200 px-4 py-2 text-sm"
    >
      <span class="font-semibold first-letter:uppercase">{{ equations?.label }}</span>
      <HelpButton v-if="equationsKey" :help-key="equationsKey" :label="equations?.label ?? ''" />
      <ElementLink v-if="index.mainModel" :pk="index.mainModel.pk" :label="modelId" mark />
      <OdeDownload v-if="system" class="ml-auto" :location="location" />
    </div>
    <ErrorState v-if="failure" :error="failure" />
    <template v-else-if="system">
      <div
        v-if="system.unsupported?.length"
        class="mx-4 mt-3 rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
        data-testid="equations-unsupported"
      >
        <span class="flex items-baseline gap-2 font-semibold">
          <span class="first-letter:uppercase">{{ unsupported?.label }}</span>
          <HelpButton
            v-if="unsupportedKey"
            :help-key="unsupportedKey"
            :label="unsupported?.label ?? ''"
          />
        </span>
        <p class="first-letter:uppercase">{{ unsupported?.summary }}</p>
        <ul class="mt-1 list-disc pl-5">
          <li v-for="(item, k) in system.unsupported" :key="k">
            {{ item.kind }}
            <ElementLink v-if="item.element" :pk="item.element" mark />
          </li>
        </ul>
      </div>
      <EquationSection
        v-for="section in sections"
        :key="section.field"
        :concept="section.concept"
        :count="section.equations.length"
      >
        <EquationRow
          v-for="(equation, k) in section.equations"
          :key="k"
          :equation="equation"
          :selected="!!selected && equation.variable === selected"
          :show-origin="section.mixed"
        />
      </EquationSection>
      <EquationSection
        v-if="system.events?.length"
        concept="odeEvents"
        :count="system.events.length"
      >
        <EquationEvent
          v-for="(event, k) in system.events"
          :key="k"
          :event="event"
          :selected="selected"
        />
      </EquationSection>
    </template>
  </div>
</template>
