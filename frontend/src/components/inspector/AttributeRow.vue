<script setup lang="ts">
defineProps<{ label: string }>();
</script>

<template>
  <div
    class="grid grid-cols-[10rem_minmax(0,1fr)] gap-x-3 border-b border-gray-100 py-1 text-sm"
    data-testid="attribute-row"
  >
    <dt class="truncate text-gray-500" :title="label">{{ label }}</dt>
    <dd class="min-w-0 break-words"><slot /></dd>
  </div>
</template>
