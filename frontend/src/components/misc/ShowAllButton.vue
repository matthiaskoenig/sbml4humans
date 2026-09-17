<script setup lang="ts">
/** The small text button below a capped list: "show all" reveals the rest of the list, "resolve
 * all" resolves the annotation resources the automatic budget left unresolved. */
withDefaults(defineProps<{ count: number; label?: "show all" | "resolve all" }>(), {
  label: "show all",
});
defineEmits<{ click: [] }>();
</script>

<template>
  <button
    type="button"
    class="text-xs text-link hover:underline"
    :data-testid="label === 'resolve all' ? 'resolve-all' : 'show-all'"
    @click="$emit('click')"
  >
    {{ label }} ({{ count }})
  </button>
</template>
