<script setup lang="ts">
import { ChevronDownIcon } from "@lucide/vue";

// the attributes (data-testid, aria-label) belong to the select, not to the wrapper
defineOptions({ inheritAttrs: false });

/** `size` "xs" is the select of a line of small text, such as the filters of the validation. */
withDefaults(
  defineProps<{ options: readonly { label: string; value: string }[]; size?: "sm" | "xs" }>(),
  { size: "sm" },
);
const model = defineModel<string>({ required: true });
</script>

<template>
  <!-- the select shrinks below the width of its longest option and truncates it, so that the bar
  of a narrow window keeps its menu button in view -->
  <span class="relative inline-flex min-w-0 items-center">
    <select
      v-bind="$attrs"
      v-model="model"
      class="max-w-72 min-w-0 cursor-pointer appearance-none truncate rounded border border-gray-300 bg-white pr-7 pl-2 hover:border-gray-400 focus:border-link focus:outline-none"
      :class="size === 'xs' ? 'py-0.5 text-xs' : 'py-1 text-sm'"
    >
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <ChevronDownIcon class="pointer-events-none absolute right-2 size-3 text-gray-500" />
  </span>
</template>
