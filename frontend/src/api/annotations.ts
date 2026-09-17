import { getAnnotationResource } from "@/api/client";
import type { AnnotationInfo } from "@/api/types";

/** At most this many resolve requests run at the same time; further resolves wait in a FIFO
 * queue. Opening an element can otherwise start one request per annotated resource in the same
 * tick (a Recon3D reaction carries up to 258 of them). */
export const MAX_CONCURRENT_RESOLVES = 4;

/** At most this many of an element's automatically shown annotation resources resolve without a
 * click. An element with many CV terms can otherwise still add up to a large number of requests
 * even with the per term and per list limits in place. Revealing more with a "show all" click is
 * a user action and is not bound by this budget. */
export const MAX_AUTO_RESOLVES = 100;

const cache = new Map<string, Promise<AnnotationInfo>>();
const queue: { resource: string; run: () => void }[] = [];
let active = 0;

function runNext(): void {
  if (active >= MAX_CONCURRENT_RESOLVES) return;
  const next = queue.shift();
  if (!next) return;
  active += 1;
  next.run();
}

/** Drop `resource`'s queued resolve and its cache entry if the request has not started yet.
 * Does nothing once the request is in flight or has settled, so a resolve that has already
 * started always runs to completion. */
function dropIfQueued(resource: string): void {
  const index = queue.findIndex((item) => item.resource === resource);
  if (index === -1) return;
  queue.splice(index, 1);
  cache.delete(resource);
}

/** Resolve an annotation resource once; concurrent and later calls share the result. At most
 * MAX_CONCURRENT_RESOLVES requests are in flight at the same time, further resolves wait in a
 * FIFO queue. A caller that stops needing the resource passes an AbortSignal: aborting it drops
 * the resolve from the queue while it has not started an actual request yet, and the resource
 * can be requested again later; a resolve that has already started keeps running and still
 * fills the cache. */
export function resolveAnnotation(resource: string, signal?: AbortSignal): Promise<AnnotationInfo> {
  let pending = cache.get(resource);
  if (!pending) {
    pending = new Promise<AnnotationInfo>((resolve, reject) => {
      queue.push({
        resource,
        run: () => {
          getAnnotationResource(resource)
            .then(resolve, reject)
            .finally(() => {
              active -= 1;
              runNext();
            });
        },
      });
      runNext();
    }).catch((error: unknown) => {
      cache.delete(resource);
      throw error;
    });
    cache.set(resource, pending);
  }
  signal?.addEventListener("abort", () => dropIfQueued(resource));
  return pending;
}

/** For the tests. */
export function resetAnnotationCache(): void {
  cache.clear();
  queue.length = 0;
  active = 0;
}
