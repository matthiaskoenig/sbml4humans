<script setup lang="ts">
import HelpLink from "@/components/help/HelpLink.vue";
import { requiredWord } from "@/components/help/words";
import type { HelpEntry } from "@/report/glossaryDetails";

/** The attributes of a type, one row each, in the order of the glossary, and behind them the row
 * which leads to the common attributes every element carries. Every row is a link which opens
 * the entry it shows, so the type of a row is the plain word of its entry and not a link of its
 * own: a link inside a link is no link at all. */
defineProps<{ rows: { key: string; entry: HelpEntry }[] }>();
</script>

<template>
  <!-- the rows read as a table where the dialog is wide enough for four columns, and stack the
  meaning of an attribute under its name where it is not. Every row is a grid of its own, as every
  row is a link of its own, so the three columns in front of the meaning have a width instead of
  the width of their content: the columns of the rows line up under each other, whatever stands
  in them, and the name of the longest attribute is cut rather than pushing the table apart -->
  <div class="@container text-sm">
    <HelpLink
      v-for="row in rows"
      :key="row.key"
      :help-key="row.key"
      class="grid grid-cols-1 items-baseline gap-x-3 border-b border-gray-100 py-1.5 hover:bg-gray-50 @md:grid-cols-[11rem_7rem_4rem_minmax(0,1fr)]"
      data-testid="help-attribute-row"
    >
      <!-- the name of the attribute, its data type and whether it is required are three columns
      of the table and one line of a stacked row, which `contents` turns them into -->
      <span class="flex flex-wrap items-baseline gap-x-2 @md:contents">
        <span class="truncate font-mono text-link">{{ row.entry.label }}</span>
        <span class="truncate font-mono text-xs text-gray-500">{{ row.entry.type?.label }}</span>
        <span class="text-xs text-gray-500">{{
          row.entry.required === undefined ? "" : requiredWord(row.entry.required)
        }}</span>
      </span>
      <span class="text-gray-700">{{ row.entry.summary }}</span>
    </HelpLink>
  </div>
</template>
