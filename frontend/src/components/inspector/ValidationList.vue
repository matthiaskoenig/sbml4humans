<script setup lang="ts">
import { computed, ref } from "vue";

import HelpLabel from "@/components/help/HelpLabel.vue";
import SelectInput from "@/components/input/SelectInput.vue";
import ElementLink from "@/components/misc/ElementLink.vue";
import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { conceptEntry, conceptKey, ruleKey } from "@/report/glossary";
import type { ReportIndex } from "@/report/index";
import { groupByRule, SEVERITY_ORDER, type Severity } from "@/report/validation";

/** Every issue of the document in the inspector of the document, a rule once with the elements it
 * concerns, filtered by severity and by category. A link selects the element, and the back button
 * returns here, as the selection is part of the route. */
const props = defineProps<{ index: ReportIndex }>();
const validation = conceptEntry("validation");
const rule = conceptEntry("validationRule");
const category = conceptEntry("validationCategory");

const shown = ref<Set<Severity>>(new Set(SEVERITY_ORDER));
const chosenCategory = ref<string>("");
/** The severities the document has, the only ones worth a filter. */
const present = computed(() => SEVERITY_ORDER.filter((s) => props.index.issueCounts[s] > 0));
const categoryOptions = computed(() => [
  { label: "all categories", value: "" },
  ...[...new Set(props.index.issues.map((i) => i.category))]
    .sort()
    .map((c) => ({ label: c, value: c })),
]);
const groups = computed(() =>
  groupByRule(
    props.index.issues.filter(
      (i) =>
        shown.value.has(i.severity) &&
        (chosenCategory.value === "" || i.category === chosenCategory.value),
    ),
  ).map((group) => ({
    ...group,
    pks: [...new Set(group.issues.map((i) => i.pk))],
    // the text of the rule as the entry of the type of its first element states it
    help: ruleKey(group.rule, props.index.get(group.issues[0]!.pk)?.sbmlType),
  })),
);

function toggle(severity: Severity): void {
  const next = new Set(shown.value);
  if (next.has(severity)) next.delete(severity);
  else next.add(severity);
  shown.value = next;
}
</script>

<template>
  <section class="mb-3" data-testid="validation-list">
    <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
      <HelpLabel :help-key="conceptKey('validation')" :tooltip="validation?.summary">{{
        validation?.label
      }}</HelpLabel>
    </h3>
    <p
      v-if="index.issues.length === 0"
      class="text-sm text-gray-600"
      data-testid="no-validation-issues"
    >
      libsbml found no errors or warnings.
    </p>
    <template v-else>
      <div class="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        <label
          v-for="severity in present"
          :key="severity"
          class="flex cursor-pointer items-center gap-1"
        >
          <input
            type="checkbox"
            class="size-3.5 accent-gray-700 max-md:size-5"
            :checked="shown.has(severity)"
            :data-testid="`validation-filter-${severity}`"
            @change="toggle(severity)"
          />
          <SeverityIcon :severity="severity" />{{ severity }}
          <span class="text-gray-500 tabular-nums">{{ index.issueCounts[severity] }}</span>
        </label>
        <SelectInput
          v-if="categoryOptions.length > 2"
          v-model="chosenCategory"
          v-tooltip.bottom="category?.summary"
          :options="categoryOptions"
          size="xs"
          :aria-label="category?.label"
          data-testid="validation-filter-category"
        />
      </div>
      <ul class="divide-y divide-gray-100 text-sm">
        <li v-for="group in groups" :key="group.rule" class="py-1.5" data-testid="validation-group">
          <details>
            <summary class="flex cursor-pointer items-start gap-2">
              <SeverityIcon :severity="group.severity" size="md" class="mt-0.5" />
              <span
                class="font-mono text-xs leading-5"
                :class="group.help ? 'text-link' : 'text-gray-600'"
                data-testid="validation-rule"
                ><HelpLabel :help-key="group.help" :tooltip="rule?.summary">{{
                  group.rule
                }}</HelpLabel></span
              >
              <span class="min-w-0 flex-1">{{ group.shortMessage }}</span>
              <span
                class="text-xs leading-5 text-gray-500 tabular-nums"
                data-testid="validation-group-count"
                >{{ group.issues.length }}</span
              >
            </summary>
            <div class="mt-1 flex flex-wrap gap-1 pl-6 text-xs">
              <ElementLink
                v-for="pk in group.pks"
                :key="pk"
                :pk="pk"
                mark
                class="rounded border border-gray-200 px-1.5 py-0.5 hover:bg-gray-50"
              />
            </div>
          </details>
        </li>
      </ul>
    </template>
  </section>
</template>
