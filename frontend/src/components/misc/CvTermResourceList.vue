<script setup lang="ts">
import { reactive, watchEffect } from "vue";

import { resolveAnnotation } from "@/api/annotations";
import type { AnnotationInfo } from "@/api/types";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { useLimitedList } from "@/report/limitedList";
import { isHttpUrl } from "@/report/text";

/** The resources of one CV term of `CvTermList`, shown and resolved up to LIST_LIMIT at a time:
 * a reaction of Recon3D carries up to 258 of them. */
const props = defineProps<{ resources: string[] }>();
const resolved = reactive(new Map<string, AnnotationInfo | null>());
// Non reactive: which resources were already requested, so a display reset can never re-trigger
// a fetch. Keyed by the resource itself, so a component instance the inspector reuses for another
// element still requests that element's resources, since they are not in this set yet.
const started = new Set<string>();

const { shown, hiddenCount, showAll } = useLimitedList(() => props.resources);

watchEffect(() => {
  for (const resource of shown.value) {
    if (started.has(resource)) continue;
    started.add(resource);
    resolveAnnotation(resource)
      .then((info) => resolved.set(resource, info))
      .catch(() => undefined);
  }
});

function href(resource: string): string {
  return isHttpUrl(resource)
    ? resource
    : `https://identifiers.org/${resource.replace(/^urn:miriam:/, "")}`;
}
</script>

<template>
  <ul class="ml-2 flex flex-col gap-0.5">
    <li v-for="resource in shown" :key="resource" data-testid="cvterm-resource">
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
  <ShowAllButton v-if="hiddenCount > 0" :count="hiddenCount" class="mt-1" @click="showAll" />
</template>
