import { createReader } from "@sbml4humans/core";
import { compileReader } from "@sbml4humans/core/wasm";

import wasmUrl from "../../vendor/sbml4humans-core/runtime/sbml4humans-core.wasm?url";
import type { ReportResponse } from "@/api/types";

/** The browser source budget, passed explicitly to the shared source API. */
export const MAX_SOURCE_BYTES = 100 * 1024 * 1024;

/** Shared immutable compiled code; each load owns and disposes its worker and memory. */
let compiled: Promise<WebAssembly.Module> | undefined;

function module(): Promise<WebAssembly.Module> {
  if (compiled === undefined) {
    const pending = compileReader(wasmUrl).catch((error: unknown) => {
      if (compiled === pending) compiled = undefined;
      throw error;
    });
    compiled = pending;
  }
  return compiled;
}

function aborted(): DOMException {
  return new DOMException("The report was cancelled", "AbortError");
}

/** Cancel waiting even when byte reads or shared compilation cannot themselves be cancelled. */
function abortable<T>(promise: Promise<T>, signal: AbortSignal): Promise<T> {
  if (signal.aborted) return Promise.reject(aborted());
  return new Promise((resolve, reject) => {
    const cancel = () => reject(aborted());
    signal.addEventListener("abort", cancel, { once: true });
    promise.then(resolve, reject).finally(() => signal.removeEventListener("abort", cancel));
  });
}

/** Build the complete report envelope locally; validation and exports retain their source. */
export async function readSource(
  input: File | string,
  signal: AbortSignal,
): Promise<ReportResponse> {
  if (signal.aborted) throw aborted();
  if ((typeof input === "string" ? input.length : input.size) > MAX_SOURCE_BYTES) {
    throw new Error("The source is larger than the 100 MB browser limit.");
  }
  // Text stays immutable until the worker encodes it; large pastes do not block the UI.
  const bytes = typeof input === "string" ? input : await abortable(input.arrayBuffer(), signal);
  const code = await abortable(module(), signal);
  if (signal.aborted) throw aborted();
  const creating = createReader({
    source: code,
    workerFactory: () =>
      new Worker(new URL("../../vendor/sbml4humans-core/worker.mjs", import.meta.url), {
        type: "module",
      }),
  });
  // A worker which finishes startup after cancellation must also release its memory.
  const reader = await abortable(creating, signal).catch((error: unknown) => {
    void creating.then(
      (reader) => reader.dispose(),
      () => {},
    );
    throw error;
  });
  try {
    return await reader.source(bytes, {
      signal,
      transfer: true,
      limits: { maxContentSize: MAX_SOURCE_BYTES },
    });
  } finally {
    reader.dispose();
  }
}
