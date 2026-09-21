<script setup lang="ts">
import { MenuIcon } from "@lucide/vue";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import logo from "@/assets/logo.png";
import { issueUrl } from "@/feedback";
import { DOCS_URL } from "@/report/glossary";
import { useReportStore } from "@/stores/report";

const route = useRoute();
const store = useReportStore();

/** The report routes show the report of the store, every other page shows none. */
const feedbackUrl = computed(() =>
  issueUrl({
    fullPath: route.fullPath,
    path: route.path,
    source: route.name === "example" || route.name === "report" ? store.source : null,
  }),
);

/** A window below `lg` holds the links of the bar behind the menu button: between `md` and `lg`
 * the bar has the search and the context of a report in its one row, and no room left for them. The menu closes with the
 * page it opened, with Escape and with a click outside of it. */
const open = ref(false);
const menu = ref<HTMLElement | null>(null);

watch(
  () => route.fullPath,
  () => (open.value = false),
);

function onKeydown(event: KeyboardEvent): void {
  if (event.key === "Escape") open.value = false;
}

function onPointerDown(event: PointerEvent): void {
  if (open.value && !menu.value?.contains(event.target as Node)) open.value = false;
}

onMounted(() => {
  document.addEventListener("keydown", onKeydown);
  document.addEventListener("pointerdown", onPointerDown);
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKeydown);
  document.removeEventListener("pointerdown", onPointerDown);
});
</script>

<template>
  <!-- a narrow window wraps the bar: the logo, the context and the menu are its first row and the
  search of the report page a second one, as wide as the window -->
  <header
    class="flex min-h-12 shrink-0 flex-wrap items-center gap-x-4 border-b border-gray-200 bg-white px-4 md:flex-nowrap"
    data-testid="app-bar"
  >
    <RouterLink
      to="/"
      class="flex shrink-0 items-center gap-2 text-base font-semibold tracking-tight text-gray-900 hover:text-link"
    >
      <img :src="logo" alt="The logo of SBML4Humans" class="size-6" data-testid="app-logo" />
      SBML4Humans
    </RouterLink>
    <div class="order-last w-full empty:hidden max-md:pb-2 md:order-none md:w-auto">
      <slot name="search" />
    </div>
    <!-- the first row of the bar keeps the height of `h-12` with the border of the bar, the bar
    itself grows with the row of the search -->
    <div class="flex h-[calc(3rem-1px)] min-w-0 flex-1 items-center gap-3">
      <slot name="context" />
    </div>
    <div ref="menu" class="relative flex items-center">
      <button
        type="button"
        class="-mr-2 flex size-10 items-center justify-center rounded text-gray-600 hover:bg-gray-100 lg:hidden"
        aria-label="menu"
        aria-controls="app-bar-links"
        :aria-expanded="open"
        data-testid="app-bar-menu"
        @click="open = !open"
      >
        <MenuIcon class="size-5" />
      </button>
      <!-- one set of links: a row of the bar on a wide window, the list of the menu on a narrow
      one -->
      <nav
        id="app-bar-links"
        class="max-lg:absolute max-lg:top-full max-lg:right-0 max-lg:z-30 max-lg:min-w-44 max-lg:flex-col max-lg:rounded max-lg:border max-lg:border-gray-200 max-lg:bg-white max-lg:py-1 max-lg:shadow-lg lg:flex lg:items-center lg:gap-3 max-lg:[&>a]:px-4 max-lg:[&>a]:py-2.5"
        :class="open ? 'flex' : 'hidden'"
        data-testid="app-bar-links"
      >
        <a
          :href="DOCS_URL"
          target="_blank"
          rel="noopener"
          class="text-sm text-gray-600 hover:text-link"
          data-testid="app-bar-docs"
          >Documentation</a
        >
        <RouterLink
          :to="{ name: 'examples' }"
          class="text-sm text-gray-600 hover:text-link"
          data-testid="app-bar-examples"
          >Examples</RouterLink
        >
        <!-- feedback is an issue of the repository, which opens with the build, the page and the
      model already written, so that a reader only has to say what they saw -->
        <a
          v-tooltip.bottom="'Open an issue on GitHub'"
          :href="feedbackUrl"
          target="_blank"
          rel="noopener"
          class="text-sm text-gray-600 hover:text-link"
          data-testid="app-bar-feedback"
          >Feedback</a
        >
      </nav>
    </div>
  </header>
</template>
