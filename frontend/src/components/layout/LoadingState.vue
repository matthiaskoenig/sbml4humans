<script setup lang="ts">
import { LoaderCircleIcon } from "@lucide/vue";

defineProps<{ message: string }>();
</script>

<template>
  <div
    class="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-gray-600"
    data-testid="loading-state"
  >
    <LoaderCircleIcon class="size-6 animate-spin" />
    <p class="text-sm">{{ message }}</p>
  </div>
</template>
