import { getAnnotationResource } from "@/api/client";
import type { AnnotationInfo } from "@/api/types";

/** At most this many resolve requests run at the same time; further resolves wait in a FIFO
 * queue. Opening an element can otherwise start one request per annotated resource in the same
 * tick (a Recon3D reaction carries up to 258 of them). */
export const MAX_CONCURRENT_RESOLVES = 4;

const cache = new Map<string, Promise<AnnotationInfo>>();
const queue: (() => void)[] = [];
let active = 0;

function runNext(): void {
  if (active >= MAX_CONCURRENT_RESOLVES) return;
  const task = queue.shift();
  if (!task) return;
  active += 1;
  task();
}

/** Run `task` once fewer than MAX_CONCURRENT_RESOLVES tasks are in flight, in the order the
 * callers arrived. */
function schedule<T>(task: () => Promise<T>): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    queue.push(() => {
      task()
        .then(resolve, reject)
        .finally(() => {
          active -= 1;
          runNext();
        });
    });
    runNext();
  });
}

/** Resolve an annotation resource once; concurrent and later calls share the result. */
export function resolveAnnotation(resource: string): Promise<AnnotationInfo> {
  let pending = cache.get(resource);
  if (!pending) {
    pending = schedule(() => getAnnotationResource(resource)).catch((error: unknown) => {
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
  queue.length = 0;
  active = 0;
}
