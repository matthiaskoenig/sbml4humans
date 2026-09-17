<script setup lang="ts">
import { ref } from "vue";

const emit = defineEmits<{ submit: [text: string] }>();
const text = ref("");
</script>

<template>
  <form class="flex flex-col gap-2" @submit.prevent="text.trim() && emit('submit', text)">
    <textarea
      v-model="text"
      rows="12"
      required
      placeholder='<?xml version="1.0" encoding="UTF-8"?>&#10;<sbml ...>'
      class="w-full rounded border border-gray-300 p-2 font-mono text-xs focus:border-link focus:outline-none"
      data-testid="paste-input"
    />
    <button
      type="submit"
      class="self-end rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
      data-testid="paste-submit"
    >
      Create report
    </button>
  </form>
</template>
