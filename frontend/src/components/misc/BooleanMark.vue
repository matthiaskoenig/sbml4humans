<script setup lang="ts">
import { CheckIcon } from "@lucide/vue";

defineProps<{ value: boolean | null | undefined }>();
</script>

<template>
  <CheckIcon v-if="value === true" class="size-3 text-gray-700" role="img" aria-label="true" />
  <span v-else class="text-gray-400">-</span>
</template>
