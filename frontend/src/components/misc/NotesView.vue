<script setup lang="ts">
import DOMPurify from "dompurify";
import { computed } from "vue";

const props = defineProps<{ notes: string | null | undefined }>();
const html = computed(() =>
  props.notes ? DOMPurify.sanitize(props.notes, { USE_PROFILES: { html: true } }) : "",
);
</script>

<template>
  <p v-if="!html" class="text-gray-400">-</p>
  <!-- eslint-disable vue/no-v-html -->
  <div
    v-else
    class="max-w-none text-sm leading-relaxed break-words [&_a]:text-link [&_a]:underline [&_blockquote]:my-1 [&_blockquote]:border-l-2 [&_blockquote]:border-gray-300 [&_blockquote]:pl-2 [&_blockquote]:text-gray-600 [&_code]:font-mono [&_code]:text-xs [&_dd]:mb-1 [&_dd]:ml-4 [&_dt]:font-semibold [&_h1]:mt-3 [&_h1]:mb-1 [&_h1]:text-base [&_h1]:font-semibold [&_h1]:first:mt-0 [&_h2]:mt-3 [&_h2]:mb-1 [&_h2]:text-sm [&_h2]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1 [&_h3]:text-sm [&_h3]:font-semibold [&_h4]:mt-2 [&_h4]:mb-1 [&_h4]:text-sm [&_h4]:font-semibold [&_h5]:mt-2 [&_h5]:mb-1 [&_h5]:text-xs [&_h5]:font-semibold [&_h6]:mt-2 [&_h6]:mb-1 [&_h6]:text-xs [&_h6]:font-semibold [&_hr]:my-3 [&_hr]:border-gray-200 [&_img]:my-1 [&_img]:max-w-full [&_li]:my-0.5 [&_ol]:my-1 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-1 [&_pre]:my-1 [&_pre]:overflow-x-auto [&_pre]:rounded [&_pre]:bg-gray-50 [&_pre]:p-2 [&_pre]:break-words [&_pre]:whitespace-pre-wrap [&_table]:my-2 [&_table]:w-full [&_table]:border-collapse [&_td]:border [&_td]:border-gray-200 [&_td]:px-2 [&_td]:py-1 [&_td]:align-top [&_th]:border [&_th]:border-gray-200 [&_th]:bg-gray-50 [&_th]:px-2 [&_th]:py-1 [&_th]:text-left [&_ul]:my-1 [&_ul]:list-disc [&_ul]:pl-5"
    data-testid="notes"
    v-html="html"
  />
  <!-- eslint-enable vue/no-v-html -->
</template>
