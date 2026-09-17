<script setup lang="ts">
import { ChevronDownIcon } from "@lucide/vue";

// the attributes (data-testid, aria-label) belong to the select, not to the wrapper
defineOptions({ inheritAttrs: false });

defineProps<{ options: readonly { label: string; value: string }[] }>();
const model = defineModel<string>({ required: true });
</script>

<template>
  <span class="relative inline-flex items-center">
    <select
      v-bind="$attrs"
      v-model="model"
      class="max-w-72 cursor-pointer appearance-none truncate rounded border border-gray-300 bg-white py-1 pr-7 pl-2 text-sm hover:border-gray-400 focus:border-link focus:outline-none"
    >
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <ChevronDownIcon class="pointer-events-none absolute right-2 size-3 text-gray-500" />
  </span>
</template>
