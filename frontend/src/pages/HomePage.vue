<script setup lang="ts">
import AppBar from "@/components/layout/AppBar.vue";
</script>

<template>
  <AppBar />
  <main class="mx-auto w-full max-w-3xl flex-1 px-4 py-10" data-testid="home-page">
    <h1 class="text-3xl font-semibold tracking-tight">SBML4Humans</h1>
    <p class="mt-2 text-gray-600">Interactive, human readable reports of SBML models.</p>
  </main>
</template>
