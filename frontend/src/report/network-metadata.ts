import { computed, onBeforeUnmount, shallowRef, watch, type ComputedRef } from "vue";
import { resolveAnnotation } from "@/api/annotations";
import type { AnnotationResource } from "@/types/annotation";
import type { NetworkNode, NetworkProjection } from "@/report/network";

export type NetworkLabels = "id" | "name" | "annotation";
export interface NetworkMetadata {
  state: "loading" | "resolved" | "failed";
  label?: string;
  resource?: AnnotationResource;
  index: NetworkNode["index"];
}

/** Identity annotations take precedence over annotations describing a class or part. */
export function identityResources(node: NetworkNode): string[] {
  const terms = node.element?.cvterms ?? [];
  const ordered = [
    ...terms.filter((term) => term.qualifier === "BQB_IS"),
    ...terms.filter((term) => term.qualifier === "BQB_IS_VERSION_OF"),
  ];
  return [...new Set(ordered.flatMap((term) => term.resources ?? []))]
    .filter((resource) => !/(?:\/|:)sbo(?:\/|:)/i.test(resource))
    .slice(0, 2);
}

export function annotationLabel(resource: AnnotationResource): string | undefined {
  if (resource.errors?.length) return undefined;
  if (
    resource.collection?.prefix.toLowerCase() === "sbo" ||
    resource.ontology?.ontology?.toLowerCase() === "sbo"
  )
    return undefined;
  return resource.uniprot?.name || resource.ontology?.label || undefined;
}

/** Uses the report resolver, including its shared cache, concurrency limit and abort queue. */
export function useNetworkMetadata(
  nodes: ComputedRef<NetworkNode[]>,
  targets: ComputedRef<string[]>,
) {
  const metadata = shallowRef(new Map<string, NetworkMetadata>());
  const jobs = new Map<string, { controller: AbortController; index: NetworkNode["index"] }>();
  let disposed = false;
  const put = (id: string, value: NetworkMetadata) => {
    metadata.value = new Map(metadata.value).set(id, value);
  };
  watch(
    [nodes, targets],
    () => {
      const byId = new Map(nodes.value.map((node) => [node.id, node]));
      const wanted = new Set(targets.value);
      const nextMetadata = new Map(metadata.value);
      for (const [id, value] of nextMetadata)
        if (byId.get(id)?.index !== value.index || (!wanted.has(id) && value.state === "failed"))
          nextMetadata.delete(id);
      if (nextMetadata.size !== metadata.value.size) metadata.value = nextMetadata;
      for (const [id, job] of jobs)
        if (!wanted.has(id) || byId.get(id)?.index !== job.index) {
          job.controller.abort();
          jobs.delete(id);
          const next = new Map(metadata.value);
          if (next.get(id)?.state === "loading") next.delete(id);
          metadata.value = next;
        }
      for (const id of wanted) {
        const node = byId.get(id);
        if (!node) continue;
        const resources = identityResources(node);
        if (!resources.length) continue;
        const previous = metadata.value.get(id);
        if (jobs.has(id) || (previous?.index === node.index && previous.state !== "loading"))
          continue;
        const controller = new AbortController(),
          job = { controller, index: node.index };
        jobs.set(id, job);
        put(id, { state: "loading", index: node.index });
        void (async () => {
          let last: AnnotationResource | undefined;
          try {
            for (const resource of resources) {
              try {
                last = await resolveAnnotation(resource, controller.signal);
              } catch {
                if (controller.signal.aborted || disposed || jobs.get(id) !== job) return;
                continue;
              }
              if (controller.signal.aborted || disposed || jobs.get(id) !== job) return;
              const label = annotationLabel(last);
              if (label) {
                put(id, { state: "resolved", label, resource: last, index: node.index });
                return;
              }
            }
            put(id, {
              state: !last || last.errors?.length ? "failed" : "resolved",
              resource: last,
              index: node.index,
            });
          } catch {
            if (!controller.signal.aborted && !disposed)
              put(id, { state: "failed", index: node.index });
          } finally {
            if (jobs.get(id) === job) jobs.delete(id);
          }
        })();
      }
    },
    { immediate: true },
  );
  onBeforeUnmount(() => {
    disposed = true;
    for (const job of jobs.values()) job.controller.abort();
    jobs.clear();
  });
  return {
    metadata,
    pending: computed(
      () => [...metadata.value.values()].filter((value) => value.state === "loading").length,
    ),
  };
}

export function resolvedNodeLabel(
  node: NetworkNode,
  metadata: ReadonlyMap<string, NetworkMetadata>,
): string | undefined {
  const value = metadata.get(node.id);
  return value?.index === node.index ? value.label : undefined;
}

export function networkLabels(
  projection: NetworkProjection,
  mode: NetworkLabels,
  metadata: ReadonlyMap<string, NetworkMetadata>,
): string[] {
  return projection.nodes.map((node) =>
    mode === "id"
      ? node.label!
      : mode === "annotation"
        ? resolvedNodeLabel(node, metadata) || node.name || node.label!
        : node.name || node.label!,
  );
}
