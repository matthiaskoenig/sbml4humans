<script setup lang="ts" generic="T extends object">
import ValueText from "@/components/misc/ValueText.vue";

defineProps<{ rows: T[]; columns: { key: string; header: string }[] }>();

function cell(row: T, key: string): string | number | null {
  const value = (row as Record<string, unknown>)[key];
  return typeof value === "string" || typeof value === "number" ? value : null;
}
</script>

<template>
  <p v-if="rows.length === 0" class="text-gray-400">-</p>
  <table v-else class="w-full text-xs" data-testid="nested-table">
    <thead>
      <tr class="border-b border-gray-200 text-left text-gray-500">
        <th v-for="column in columns" :key="column.key" class="py-1 pr-3 font-medium">
          {{ column.header }}
        </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, i) in rows" :key="i" class="border-b border-gray-100 align-top">
        <td v-for="column in columns" :key="column.key" class="py-1 pr-3 break-all">
          <slot :name="`cell-${column.key}`" :row="row">
            <ValueText :value="cell(row, column.key)" />
          </slot>
        </td>
      </tr>
    </tbody>
  </table>
</template>
