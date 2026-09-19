<script setup lang="ts">
import HelpLink from "@/components/help/HelpLink.vue";
import { requiredWord } from "@/components/help/words";
import type { HelpEntry } from "@/report/glossaryDetails";

/** The attributes of a type, one row each, in the order of the glossary, and behind them the row
 * which leads to the common attributes every element carries. It is a table, as it is one on the
 * reference page: a reader of a screen reader hears the name of the column in front of every cell
 * instead of a run of loose words. The name of the attribute is the link of a row, and the cells
 * next to it are text, so that no link sits inside another one. */
defineProps<{ rows: { key: string; entry: HelpEntry }[] }>();

/** The names of the columns, chrome of the dialog: the words of the table of the reference page.
 * They are read, not shown, the row itself says what its cells are. */
const COLUMNS = ["attribute", "type", "required", "meaning"] as const;
</script>

<template>
  <!-- the table lays out its columns by their content, so no name of an attribute is cut and the
  meaning takes the width which is left. Where the dialog is too narrow for four columns, on a
  telephone, the rows and their cells stop being a table: the name, the data type and whether it
  is required flow on one line, which wraps, and the meaning stands below them -->
  <!-- `relative`, because the head of the table below is hidden the way a screen reader still
  reads it, which takes it out of the flow: without a containing block of its own here it would be
  laid out against the dialog, which is positioned, and add the whole height of the table to what
  the dialog itself can scroll - and a dialog which scrolls carries its fixed header out of sight
  the moment the browser scrolls something into view -->
  <div class="@container relative">
    <table class="w-full table-auto text-sm">
      <thead class="sr-only">
        <tr>
          <th v-for="column in COLUMNS" :key="column" scope="col">{{ column }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="row.key"
          class="group block border-b border-gray-100 py-1.5 hover:bg-gray-50 @md:table-row @md:py-0"
          data-testid="help-attribute-row"
        >
          <td class="inline-block align-baseline @md:table-cell">
            <HelpLink
              :help-key="row.key"
              class="block py-0.5 pr-3 font-mono break-words text-link group-hover:underline @md:py-1.5 @md:whitespace-nowrap"
              >{{ row.entry.label }}</HelpLink
            >
          </td>
          <td
            class="inline-block pr-2 align-baseline font-mono text-xs text-gray-500 @md:table-cell @md:py-1.5 @md:pr-3 @md:whitespace-nowrap"
          >
            {{ row.entry.type?.label }}
          </td>
          <td
            class="inline-block align-baseline text-xs text-gray-500 @md:table-cell @md:py-1.5 @md:pr-3 @md:whitespace-nowrap"
          >
            {{ row.entry.required === undefined ? "" : requiredWord(row.entry.required) }}
          </td>
          <td class="block align-baseline text-gray-700 @md:table-cell @md:py-1.5">
            {{ row.entry.summary }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
