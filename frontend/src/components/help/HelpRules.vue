<script setup lang="ts">
import { CircleAlertIcon, TriangleAlertIcon } from "@lucide/vue";

import type { HelpRule } from "@/report/glossaryDetails";

/** The validation rules of the specification an entry is held to, as libsbml states them: its
 * number, which a validator reports, its severity and its message. The message is plain text and
 * names the elements it is about in angle brackets (`<species>`), so it is interpolated and never
 * rendered as markup. */
defineProps<{ rules: HelpRule[] }>();
</script>

<template>
  <ul class="space-y-1.5 text-sm">
    <li v-for="rule in rules" :key="rule.id" class="flex gap-2" data-testid="help-rule">
      <!-- the number is what a validator reports, so it is set in the font of an identifier and
      keeps its column while the messages next to it wrap over several lines -->
      <span class="shrink-0 font-mono text-xs leading-5 text-gray-500">{{ rule.id }}</span>
      <component
        :is="rule.severity === 'error' ? CircleAlertIcon : TriangleAlertIcon"
        class="mt-0.5 size-4 shrink-0"
        :class="rule.severity === 'error' ? 'text-red-600' : 'text-amber-500'"
        role="img"
        :aria-label="rule.severity"
      />
      <span class="min-w-0 text-gray-700"
        >{{ rule.message }}
        <span v-if="rule.section" class="whitespace-nowrap text-gray-500"
          >({{ rule.section }})</span
        ></span
      >
    </li>
  </ul>
</template>
