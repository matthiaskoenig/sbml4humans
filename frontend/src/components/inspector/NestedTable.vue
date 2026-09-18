<script setup lang="ts" generic="T extends object">
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useLimitedList } from "@/report/limitedList";

const props = defineProps<{ rows: T[]; columns: { key: string; header: string }[] }>();

function cell(row: T, key: string): string | number | null {
  const value = (row as Record<string, unknown>)[key];
  return typeof value === "string" || typeof value === "number" ? value : null;
}

const { shown, hiddenCount, showAll } = useLimitedList(() => props.rows);
</script>

<template>
  <p v-if="rows.length === 0" class="text-gray-400">-</p>
  <template v-else>
    <!-- a table of four columns of identifiers is wider than the pane of the inspector on a
    narrow screen, and it scrolls there instead of being cut off at the edge of the pane -->
    <div class="overflow-x-auto">
      <table class="w-full text-xs" data-testid="nested-table">
        <thead>
          <tr class="border-b border-gray-200 text-left text-gray-500">
            <th v-for="column in columns" :key="column.key" class="py-1 pr-3 font-medium">
              {{ column.header }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in shown" :key="i" class="border-b border-gray-100 align-top">
            <!-- `break-words` only breaks inside a word when the word does not fit a line of its
          own, and it leaves the minimum width of a column at the width of its longest word, so
          the automatic layout gives an identifier the column it needs instead of wrapping
          `M_atp_c` into `M_at` and `p_c`. -->
            <td v-for="column in columns" :key="column.key" class="py-1 pr-3 break-words">
              <slot :name="`cell-${column.key}`" :row="row">
                <ValueText :value="cell(row, column.key)" />
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <ShowAllButton v-if="hiddenCount > 0" :count="hiddenCount" class="mt-1" @click="showAll" />
  </template>
</template>
