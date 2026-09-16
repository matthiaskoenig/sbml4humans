<script setup lang="ts">
import { reactive, watchEffect } from "vue";

import { resolveAnnotation } from "@/api/annotations";
import type { AnnotationInfo, CVTerm } from "@/api/types";
import { isHttpUrl } from "@/report/text";

const props = defineProps<{ cvterms: CVTerm[] }>();
const resolved = reactive(new Map<string, AnnotationInfo | null>());
// Non reactive: which resources were already requested, so a display reset can never re-trigger a fetch.
const started = new Set<string>();

watchEffect(() => {
  for (const term of props.cvterms) {
    for (const resource of term.resources) {
      if (started.has(resource)) continue;
      started.add(resource);
      resolveAnnotation(resource)
        .then((info) => resolved.set(resource, info))
        .catch(() => undefined);
    }
  }
});

function href(resource: string): string {
  return isHttpUrl(resource)
    ? resource
    : `https://identifiers.org/${resource.replace(/^urn:miriam:/, "")}`;
}
</script>

<template>
  <p v-if="cvterms.length === 0" class="text-gray-400">-</p>
  <ul v-else class="flex flex-col gap-2">
    <li v-for="(term, i) in cvterms" :key="i" data-testid="cvterm">
      <p class="font-mono text-xs text-gray-500">{{ term.qualifier }}</p>
      <ul class="ml-2 flex flex-col gap-0.5">
        <li v-for="resource in term.resources" :key="resource" data-testid="cvterm-resource">
          <a
            :href="href(resource)"
            target="_blank"
            rel="noopener"
            class="break-all text-link hover:underline"
          >
            <template v-if="resolved.get(resource)?.label">{{
              resolved.get(resource)!.label
            }}</template>
            <template v-else>{{ resource }}</template>
          </a>
          <span v-if="resolved.get(resource)?.label" class="ml-1 font-mono text-xs text-gray-500">{{
            resolved.get(resource)!.term ?? resource
          }}</span>
          <p v-if="resolved.get(resource)?.description" class="text-xs text-gray-600">
            {{ resolved.get(resource)!.description }}
          </p>
        </li>
      </ul>
    </li>
  </ul>
</template>
