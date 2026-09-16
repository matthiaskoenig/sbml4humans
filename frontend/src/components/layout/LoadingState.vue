<script setup lang="ts">
defineProps<{ message: string }>();
</script>

<template>
  <div
    class="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-gray-600"
    data-testid="loading-state"
  >
    <i class="pi pi-spin pi-spinner text-2xl" />
    <p class="text-sm">{{ message }}</p>
  </div>
</template>
