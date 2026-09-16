import { getAnnotationResource } from "@/api/client";
import type { AnnotationInfo } from "@/api/types";

const cache = new Map<string, Promise<AnnotationInfo>>();

/** Resolve an annotation resource once; concurrent and later calls share the result. */
export function resolveAnnotation(resource: string): Promise<AnnotationInfo> {
  let pending = cache.get(resource);
  if (!pending) {
    pending = getAnnotationResource(resource).catch((error: unknown) => {
      cache.delete(resource);
      throw error;
    });
    cache.set(resource, pending);
  }
  return pending;
}

/** For the tests. */
export function resetAnnotationCache(): void {
  cache.clear();
}
