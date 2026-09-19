<script setup lang="ts">
import HelpLink from "@/components/help/HelpLink.vue";
import { requiredWord } from "@/components/help/words";
import type { HelpEntry } from "@/report/glossaryDetails";

/** The low level of one entry: the data type of its value, the literals of an enumeration,
 * whether the specification requires it, what holds when it is absent and the section of the
 * specification which defines it. The dialog renders this part only for an entry which has at
 * least one of them, and every row is left out where the entry says nothing. */
defineProps<{ entry: HelpEntry }>();

/** The labels of the rows, chrome of the dialog: the words the reference pages of the
 * documentation use for the same thing. */
const LABELS = {
  type: "data type",
  values: "values",
  required: "required",
  default: "Default",
  spec: "Specification",
} as const;
</script>

<template>
  <!-- a definition list as a two column grid: every value starts at one line, however long the
  label of a row is, the way the attributes of the inspector are laid out -->
  <dl class="grid grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-1 text-sm">
    <template v-if="entry.type">
      <dt class="text-gray-500">{{ LABELS.type }}</dt>
      <dd>
        <HelpLink
          :help-key="entry.type.key"
          class="rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 font-mono text-xs text-link hover:bg-gray-100"
          >{{ entry.type.label }}</HelpLink
        >
      </dd>
    </template>
    <template v-if="entry.values?.length">
      <dt class="text-gray-500">{{ LABELS.values }}</dt>
      <dd class="flex flex-wrap gap-1">
        <code
          v-for="value in entry.values"
          :key="value"
          class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs text-gray-800"
          >{{ value }}</code
        >
      </dd>
    </template>
    <template v-if="entry.required !== undefined">
      <dt class="text-gray-500">{{ LABELS.required }}</dt>
      <dd>{{ requiredWord(entry.required) }}</dd>
    </template>
    <template v-if="entry.default">
      <dt class="text-gray-500">{{ LABELS.default }}</dt>
      <dd class="text-gray-700">{{ entry.default }}</dd>
    </template>
    <template v-if="entry.spec">
      <dt class="text-gray-500">{{ LABELS.spec }}</dt>
      <dd>
        <a
          :href="entry.spec.url"
          target="_blank"
          rel="noopener"
          class="text-link hover:underline"
          >{{ entry.spec.label }}</a
        >
      </dd>
    </template>
  </dl>
</template>
