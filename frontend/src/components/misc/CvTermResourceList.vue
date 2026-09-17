<script setup lang="ts">
import { onBeforeUnmount, reactive, watch, watchEffect } from "vue";

import { resolveAnnotation } from "@/api/annotations";
import type { AnnotationInfo } from "@/api/types";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { useLimitedList } from "@/report/limitedList";
import { isHttpUrl } from "@/report/text";

/** The resources of one CV term of `CvTermList`, shown and resolved up to LIST_LIMIT at a time:
 * a reaction of Recon3D carries up to 258 of them. Only the first `autoResolveLimit` shown
 * resources resolve, in order: a resource shown beyond the limit renders as an unresolved link,
 * without a label, until `CvTermList` lifts the limit, which it does for a click on this term's
 * own "show all" (emitted as `showAll`) or on the element's "resolve all". */
const props = withDefaults(defineProps<{ resources: string[]; autoResolveLimit?: number }>(), {
  autoResolveLimit: Infinity,
});
const emit = defineEmits<{ showAll: [] }>();
const resolved = reactive(new Map<string, AnnotationInfo | null>());
// Non reactive: which resources were already requested, so a display reset can never re-trigger
// a fetch. Keyed by the resource itself, so a component instance the inspector reuses for another
// element still requests that element's resources, since they are not in this set yet.
const started = new Set<string>();
// The AbortController of every resource requested for the current list, so a resolve that has
// not started an actual request yet can be cancelled once the list moves on.
const controllers = new Map<string, AbortController>();

function cancelPending(): void {
  for (const controller of controllers.values()) controller.abort();
  controllers.clear();
  started.clear();
  resolved.clear();
}

// cancel the not yet started resolves of the previous list, forget what it requested and drop
// what it resolved, whenever the resources this list shows change (another element selected) or
// the component unmounts, so a queue slot is never held for a resource nobody looks at anymore,
// the resource is requestable again once it matters again, and a label from the previous list
// never shows for a resource this list has not resolved itself.
watch(() => props.resources, cancelPending);
onBeforeUnmount(cancelPending);

const { shown, hiddenCount, showAll } = useLimitedList(() => props.resources);

function showAllResources(): void {
  showAll();
  emit("showAll");
}

watchEffect(() => {
  const limit = props.autoResolveLimit;
  shown.value.forEach((resource, index) => {
    if (started.has(resource) || index >= limit) return;
    started.add(resource);
    const controller = new AbortController();
    controllers.set(resource, controller);
    // the bookkeeping of a settled resolve only applies while it is still this list's resolve of
    // the resource: after a list change the list may already have requested the resource again
    const current = (): boolean => controllers.get(resource) === controller;
    resolveAnnotation(resource, controller.signal)
      .then((info) => resolved.set(resource, info))
      .catch(() => undefined)
      .finally(() => {
        if (current()) controllers.delete(resource);
      });
  });
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
  <ShowAllButton
    v-if="hiddenCount > 0"
    :count="hiddenCount"
    class="mt-1 ml-2"
    @click="showAllResources"
  />
</template>
