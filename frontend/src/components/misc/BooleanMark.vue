<script setup lang="ts">
import { CheckIcon, XIcon } from "@lucide/vue";

// A boolean of the report has three states: true, false and an attribute the file does not set.
// `false` is a value, so it is a mark of its own, a thin grey cross, and only the unset attribute
// is the dash every other empty value is. The 13 px icons are inline with their bottom 2 px below
// the baseline, which centres their glyph on the capitals of the text beside it; a flex row (a
// windowed table cell) centres them.
defineProps<{ value: boolean | null | undefined }>();
</script>

<template>
  <CheckIcon
    v-if="value === true"
    class="inline-block size-3.25 align-[-2px] text-gray-700"
    role="img"
    aria-label="true"
  />
  <XIcon
    v-else-if="value === false"
    class="inline-block size-3.25 align-[-2px] text-gray-500"
    :stroke-width="1.75"
    role="img"
    aria-label="false"
  />
  <span v-else class="text-gray-400">-</span>
</template>
