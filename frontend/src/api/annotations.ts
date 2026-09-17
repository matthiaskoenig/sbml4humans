import { getAnnotationResource } from "@/api/client";
import type { AnnotationInfo } from "@/api/types";

/** At most this many resolve requests run at the same time; further resolves wait in a FIFO
 * queue. Opening an element can otherwise start one request per annotated resource in the same
 * tick (a Recon3D reaction carries up to 258 of them). */
export const MAX_CONCURRENT_RESOLVES = 4;

/** At most this many of an element's automatically shown annotation resources resolve without a
 * click. An element with many CV terms can otherwise still add up to a large number of requests
 * even with the per term and per list limits in place. Revealing more with a "show all" or
 * "resolve all" click is a user action and is not bound by this budget. */
export const MAX_AUTO_RESOLVES = 100;

/** A resolve waiting in the queue for a free request slot. */
interface QueuedResolve {
  resource: string;
  /** The callers still waiting for the resolve. A caller without a signal always counts, a
   * caller with a signal until it aborts; the resolve is dropped once no caller is left. */
  callers: number;
  /** Aborted once the resolve leaves the queue, which removes the abort listeners of its
   * callers. */
  listeners: AbortController;
  /** Starts the request. */
  start: () => void;
  /** Rejects the resolve without a request. */
  reject: (error: DOMException) => void;
}

const cache = new Map<string, Promise<AnnotationInfo>>();
// the queue in FIFO order: a Map iterates in insertion order
const queue = new Map<string, QueuedResolve>();
let active = 0;

function runNext(): void {
  if (active >= MAX_CONCURRENT_RESOLVES) return;
  const next = queue.values().next().value;
  if (!next) return;
  queue.delete(next.resource);
  next.listeners.abort();
  active += 1;
  next.start();
}

/** Drops a queued resolve whose callers all aborted: it leaves the queue and the cache without a
 * request, and its promise rejects with an AbortError, so the resource is requested again by the
 * next caller. */
function drop(queued: QueuedResolve): void {
  queue.delete(queued.resource);
  cache.delete(queued.resource);
  queued.listeners.abort();
  queued.reject(new DOMException("the resolve was cancelled before it started", "AbortError"));
}

/** Counts a caller of a queued resolve; a caller with a signal leaves again when it aborts. */
function addCaller(queued: QueuedResolve, signal: AbortSignal | undefined): void {
  queued.callers += 1;
  if (!signal) return;
  const release = (): void => {
    queued.callers -= 1;
    if (queued.callers === 0) drop(queued);
  };
  if (signal.aborted) release();
  else signal.addEventListener("abort", release, { once: true, signal: queued.listeners.signal });
}

/** Resolve an annotation resource once; concurrent and later calls share the result. At most
 * MAX_CONCURRENT_RESOLVES requests are in flight at the same time, further resolves wait in a
 * FIFO queue. A caller that stops needing the resource passes an AbortSignal: once every caller
 * of a queued resolve has aborted, the resolve is dropped before it starts a request, its promise
 * rejects with an AbortError and the resource can be requested again later. A resolve that has
 * already started keeps running and still fills the cache. */
export function resolveAnnotation(resource: string, signal?: AbortSignal): Promise<AnnotationInfo> {
  let pending = cache.get(resource);
  if (!pending) {
    const created: Promise<AnnotationInfo> = new Promise<AnnotationInfo>((resolve, reject) => {
      queue.set(resource, {
        resource,
        callers: 0,
        listeners: new AbortController(),
        start: () => {
          getAnnotationResource(resource)
            .then(resolve, reject)
            .finally(() => {
              active -= 1;
              runNext();
            });
        },
        reject,
      });
    }).catch((error: unknown) => {
      // a failed or dropped resolve leaves the cache, unless a new resolve of the same resource
      // has already taken its place
      if (cache.get(resource) === created) cache.delete(resource);
      throw error;
    });
    cache.set(resource, created);
    pending = created;
  }
  const queued = queue.get(resource);
  if (queued) addCaller(queued, signal);
  runNext();
  return pending;
}

/** For the tests. */
export function resetAnnotationCache(): void {
  // a queued entry keeps an abort listener on every caller's signal; without removing them a
  // signal left over from an earlier test could later abort and drop an entry of another test
  for (const queued of queue.values()) queued.listeners.abort();
  cache.clear();
  queue.clear();
  active = 0;
}
