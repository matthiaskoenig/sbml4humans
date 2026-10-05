<script setup lang="ts">
import { onBeforeUnmount, reactive, watch, watchEffect } from "vue";

import { resolveAnnotation } from "@/api/annotations";
import AnnotationCard, { type AnnotationCardState } from "@/components/misc/AnnotationCard.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { useLimitedList } from "@/report/limitedList";
import type { AnnotationResource } from "@/types/annotation";

/** The resources of one CV term of `CvTermList`, shown and resolved up to LIST_LIMIT at a time:
 * a reaction of Recon3D carries up to 258 of them. Only the first `autoResolveLimit` shown
 * resources resolve, in order: a resource shown beyond the limit renders as an unresolved link,
 * without a label, until `CvTermList` lifts the limit, which it does for a click on this term's
 * own "show all" (emitted as `showAll`) or on the element's "resolve all". */
const props = withDefaults(
  defineProps<{ resources: string[]; qualifier: string; autoResolveLimit?: number }>(),
  {
    autoResolveLimit: Infinity,
  },
);
const emit = defineEmits<{ showAll: [] }>();
const resolved = reactive(new Map<string, AnnotationResource>());
// the resources whose resolve failed, which the card says
const failed = reactive(new Set<string>());
// Non reactive: which resources were already requested, so a display reset can never re-trigger
// a fetch. Keyed by the resource itself, so a component instance the inspector reuses for another
// element still requests that element's resources, since they are not in this set yet.
const started = new Set<string>();
// The AbortController of every resource requested for the current list, so a resolve that has
// not started an actual request yet can be cancelled once the list moves on.
const controllers = reactive(new Map<string, AbortController>());

function cancelPending(): void {
  for (const controller of controllers.values()) controller.abort();
  controllers.clear();
  started.clear();
  resolved.clear();
  failed.clear();
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
      .catch(() => {
        if (current() && !controller.signal.aborted) failed.add(resource);
      })
      .finally(() => {
        if (current()) controllers.delete(resource);
      });
  });
});

function stateOf(resource: string): AnnotationCardState {
  if (resolved.has(resource)) return "resolved";
  if (failed.has(resource)) return "failed";
  return controllers.has(resource) ? "loading" : "idle";
}
</script>

<template>
  <ul class="flex flex-col gap-2">
    <li v-for="resource in shown" :key="resource" data-testid="cvterm-resource">
      <AnnotationCard
        :resource="resource"
        :qualifier="qualifier"
        :info="resolved.get(resource)"
        :state="stateOf(resource)"
      />
    </li>
  </ul>
  <ShowAllButton
    v-if="hiddenCount > 0"
    :count="hiddenCount"
    class="mt-1 ml-2"
    @click="showAllResources"
  />
</template>
