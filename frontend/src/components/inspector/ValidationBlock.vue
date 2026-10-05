<script setup lang="ts">
import type { ValidationIssue } from "@/api/types";
import HelpLabel from "@/components/help/HelpLabel.vue";
import SeverityIcon from "@/components/misc/SeverityIcon.vue";
import { useReportIndex } from "@/report/context";
import { conceptEntry, conceptKey, ruleKey } from "@/report/glossary";

/** The issues of one element, errors first: the short message, the rule, the category and the
 * severity, and the full message of libsbml behind "more". */
defineProps<{ issues: ValidationIssue[] }>();
const index = useReportIndex();
/** The entry which states the text of the rule of an issue, the one of its element first. */
function helpOf(issue: ValidationIssue): string | undefined {
  return ruleKey(issue.rule, index.value?.get(issue.pk)?.sbmlType);
}
const validation = conceptEntry("validation");
const rule = conceptEntry("validationRule");
const BOX = {
  error: "border-red-200 bg-red-50",
  warning: "border-amber-200 bg-amber-50",
  info: "border-gray-200 bg-gray-50",
} as const;
</script>

<template>
  <section v-if="issues.length" class="mb-3" data-testid="inspector-validation">
    <h3 class="mb-1 text-xs font-semibold tracking-wide text-gray-500 uppercase">
      <HelpLabel :help-key="conceptKey('validation')" :tooltip="validation?.summary">{{
        validation?.label
      }}</HelpLabel>
    </h3>
    <ul class="space-y-1.5">
      <li
        v-for="(issue, k) in issues"
        :key="k"
        class="rounded border px-2 py-1.5 text-sm"
        :class="BOX[issue.severity]"
        data-testid="validation-issue"
      >
        <div class="flex items-start gap-2">
          <SeverityIcon :severity="issue.severity" size="md" class="mt-0.5" />
          <span class="min-w-0 flex-1">
            <span class="font-medium">{{ issue.shortMessage }}</span>
            <span class="block text-xs text-gray-600">
              <!-- the number opens the entry which states the text of the rule, where the
              glossary cites it, and is plain text else -->
              <span
                class="font-mono"
                :class="{ 'text-link': helpOf(issue) }"
                data-testid="validation-rule"
                ><HelpLabel :help-key="helpOf(issue)" :tooltip="rule?.summary">{{
                  issue.rule
                }}</HelpLabel></span
              >
              · {{ issue.category }} · {{ issue.severity }}
            </span>
          </span>
        </div>
        <details class="mt-1 pl-6 text-xs text-gray-700">
          <summary class="cursor-pointer text-gray-500">more</summary>
          <!-- the message of libsbml is plain text over several lines, interpolated, never
          rendered as markup -->
          <p class="mt-0.5 break-words whitespace-pre-line">{{ issue.message }}</p>
        </details>
      </li>
    </ul>
  </section>
</template>
