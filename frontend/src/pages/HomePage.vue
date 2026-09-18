<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import logo from "@/assets/logo.png";
import FileUpload from "@/components/input/FileUpload.vue";
import PasteInput from "@/components/input/PasteInput.vue";
import UrlInput from "@/components/input/UrlInput.vue";
import AppBar from "@/components/layout/AppBar.vue";
import AppFooter from "@/components/layout/AppFooter.vue";
import ErrorState from "@/components/layout/ErrorState.vue";
import LoadingState from "@/components/layout/LoadingState.vue";
import { useReportStore } from "@/stores/report";

type Tab = "upload" | "url" | "paste";
const TABS: { id: Tab; label: string }[] = [
  { id: "upload", label: "Upload" },
  { id: "url", label: "URL" },
  { id: "paste", label: "Paste" },
];

const router = useRouter();
const store = useReportStore();
const tab = ref<Tab>("upload");

async function submit(load: () => Promise<void>, route: { url?: string } = {}): Promise<void> {
  store.clear();
  await load();
  if (!store.error)
    await router.push({ name: "report", query: route.url ? { url: route.url } : {} });
}
</script>

<template>
  <AppBar />
  <main class="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-10" data-testid="home-page">
    <h1 class="flex items-center gap-3 text-3xl font-semibold tracking-tight">
      <img :src="logo" alt="The logo of SBML4Humans" class="size-9" data-testid="app-logo" />
      SBML4Humans
    </h1>
    <p class="mt-2 text-gray-600">
      Interactive, human readable reports of
      <a href="https://sbml.org" class="text-link hover:underline">SBML</a> models.
    </p>

    <div class="mt-8 flex gap-1 border-b border-gray-200" role="tablist">
      <button
        v-for="item in TABS"
        :key="item.id"
        type="button"
        role="tab"
        :aria-selected="tab === item.id"
        class="-mb-px border-b-2 px-3 py-2 text-sm font-medium"
        :class="
          tab === item.id
            ? 'border-gray-900 text-gray-900'
            : 'border-transparent text-gray-500 hover:text-gray-800'
        "
        :data-testid="`home-tab-${item.id}`"
        @click="tab = item.id"
      >
        {{ item.label }}
      </button>
    </div>

    <div class="mt-6">
      <LoadingState
        v-if="store.loading"
        :message="`Creating the report of ${store.source?.name ?? 'the model'}`"
      />
      <template v-else>
        <FileUpload
          v-if="tab === 'upload'"
          @submit="(file) => submit(() => store.loadFile(file))"
        />
        <UrlInput
          v-else-if="tab === 'url'"
          @submit="(url) => submit(() => store.loadUrl(url), { url })"
        />
        <PasteInput v-else @submit="(text) => submit(() => store.loadContent(text))" />
        <ErrorState v-if="store.error" :error="store.error" />
      </template>
    </div>

    <p class="mt-8 text-sm text-gray-600">
      Or browse the
      <RouterLink
        :to="{ name: 'examples' }"
        class="text-link hover:underline"
        data-testid="home-examples-link"
        >examples</RouterLink
      >.
    </p>

    <AppFooter />
  </main>
</template>
