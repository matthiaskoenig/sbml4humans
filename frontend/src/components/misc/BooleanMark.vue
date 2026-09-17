<script setup lang="ts">
import { CheckIcon } from "@lucide/vue";

// The 13 px check is inline with its bottom 2 px below the baseline, which centres its glyph of
// 11 x 8 px on the capitals of the text beside it; a flex row (a windowed table cell) centres it.
defineProps<{ value: boolean | null | undefined }>();
</script>

<template>
  <CheckIcon
    v-if="value === true"
    class="inline-block size-3.25 align-[-2px] text-gray-700"
    role="img"
    aria-label="true"
  />
  <span v-else class="text-gray-400">-</span>
</template>
