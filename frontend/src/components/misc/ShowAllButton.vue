<script setup lang="ts">
defineProps<{ count: number }>();
defineEmits<{ click: [] }>();
</script>

<template>
  <button
    type="button"
    class="text-xs text-link hover:underline"
    data-testid="show-all"
    @click="$emit('click')"
  >
    show all ({{ count }})
  </button>
</template>
