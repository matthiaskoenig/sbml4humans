<script setup lang="ts">
import { onBeforeUnmount, reactive, watch, watchEffect } from "vue";

import { resolveAnnotation } from "@/api/annotations";
import type { AnnotationInfo } from "@/api/types";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { useLimitedList } from "@/report/limitedList";
import { isHttpUrl } from "@/report/text";

/** The resources of one CV term of `CvTermList`, shown and resolved up to LIST_LIMIT at a time:
 * a reaction of Recon3D carries up to 258 of them. `autoResolveLimit` restricts the automatic
 * resolution to that many of the shown resources, in order, until this term's own "show all" is
 * clicked: a resource shown beyond the limit renders as an unresolved link, without a label,
 * until it is requested by a later show all click or the element-wide budget frees up again for
 * another element. */
const props = withDefaults(defineProps<{ resources: string[]; autoResolveLimit?: number }>(), {
  autoResolveLimit: Infinity,
});
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
}

// cancel the not yet started resolves of the previous list and forget what it requested
// whenever the resources this list shows change (another element selected) or the component
// unmounts, so a queue slot is never held for a resource nobody looks at anymore and the
// resource is requestable again once it matters again.
watch(() => props.resources, cancelPending);
onBeforeUnmount(cancelPending);

const { shown, hiddenCount, showAll, expanded } = useLimitedList(() => props.resources);

watchEffect(() => {
  // once this term is expanded by its own show all, every shown resource resolves: revealing it
  // was a user action and is not bound by the automatic resolution budget.
  const limit = expanded.value ? Infinity : props.autoResolveLimit;
  shown.value.forEach((resource, index) => {
    if (started.has(resource) || index >= limit) return;
    started.add(resource);
    const controller = new AbortController();
    controllers.set(resource, controller);
    resolveAnnotation(resource, controller.signal)
      .then((info) => resolved.set(resource, info))
      .catch(() => undefined)
      .finally(() => controllers.delete(resource));
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
  <ShowAllButton v-if="hiddenCount > 0" :count="hiddenCount" class="mt-1" @click="showAll" />
</template>
