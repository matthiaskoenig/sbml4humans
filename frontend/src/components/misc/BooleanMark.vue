<script setup lang="ts">
defineProps<{ value: boolean | null | undefined }>();
</script>

<template>
  <i v-if="value === true" class="pi pi-check text-xs text-gray-700" aria-label="true" />
  <span v-else class="text-gray-400">-</span>
</template>
