<script setup lang="ts">
/** One part of the body of the help dialog under its heading, in the small grey capitals the
 * inspector heads its columns with. The dialog decides which parts an entry has, so a section
 * which is rendered always holds something. */
defineProps<{ title: string }>();
</script>

<template>
  <section class="mt-4">
    <h3 class="mb-1.5 text-xs font-semibold tracking-wide text-gray-500 uppercase">{{ title }}</h3>
    <slot />
  </section>
</template>
