import { compileReader } from "./wasm.mjs";

function aborted() { return new DOMException("The SBML report was cancelled.", "AbortError"); }

/** Parse reports off the UI thread. Cancellation replaces the active worker. */
export async function createReader({ source, workerFactory } = {}) {
  const module = await compileReader(source);
  if (!workerFactory) {
    if (typeof Worker === "function") workerFactory = () => new Worker(new URL("./worker.mjs", import.meta.url), { type: "module" });
    else {
      const nodeWorkers = "node:worker_threads";
      const { Worker: NodeWorker } = await import(/* @vite-ignore */ nodeWorkers);
      workerFactory = () => new NodeWorker(new URL("./worker.mjs", import.meta.url));
    }
  }
  const queue = [];
  let startedResolve, startedReject;
  const started = new Promise((resolve, reject) => { startedResolve = resolve; startedReject = reject; });
  let worker;
  let active;
  let ready = false;
  let disposed = false;
  let sequence = 0;
  function finish(job, error, result) {
    job.signal?.removeEventListener("abort", job.abort);
    if (error) job.reject(error); else job.resolve(result);
  }
  function dispatch() {
    if (disposed || !ready || active || !queue.length) return;
    active = queue.shift();
    try { worker.postMessage({ type: active.type, id: active.id, source: active.source, options: active.options }, typeof active.source === "string" ? [] : [active.source]); }
    catch (error) { const job = active; active = undefined; finish(job, error); dispatch(); }
  }
  function restart() {
    if (disposed) return;
    ready = false;
    worker?.terminate();
    const current = worker = workerFactory();
    const receive = (message) => {
      if (current !== worker || disposed) return;
      if (message.type === "ready") { ready = true; startedResolve(); dispatch(); return; }
      if (!ready && message.type === "error") { failed(new Error(message.message)); return; }
      if (message.id !== active?.id) return;
      const job = active;
      active = undefined;
      const error = message.type === "error" ? Object.assign(new Error(message.message), { kind: message.kind }) : undefined;
      finish(job, error, message.result);
      if (message.fatal) restart(); else dispatch();
    };
    const failed = (error) => {
      if (current !== worker || disposed) return;
      const failure = error instanceof Error ? error : new Error(error.message);
      if (active) { finish(active, failure); active = undefined; }
      if (!ready) {
        disposed = true; startedReject(failure); current.terminate();
        for (const job of queue.splice(0)) finish(job, failure);
      } else restart();
    };
    if (typeof current.addEventListener === "function") {
      current.addEventListener("message", (event) => receive(event.data));
      current.addEventListener("error", failed);
    } else {
      current.on("message", receive); current.on("error", failed);
      current.on("exit", () => { if (current === worker && !disposed) failed(new Error("The SBML parser worker ended.")); });
    }
    current.postMessage({ type: "init", module });
  }
  restart();
  await started;
  function submit(type, input, { signal, transfer = false, ...options } = {}) {
    if (disposed) return Promise.reject(new Error("The SBML reader is disposed."));
    if (signal?.aborted) return Promise.reject(aborted());
    let source;
    if (typeof input === "string") source = input;
    else {
      const bytes = input instanceof ArrayBuffer ? new Uint8Array(input) : new Uint8Array(input.buffer, input.byteOffset, input.byteLength);
      source = transfer && bytes.buffer instanceof ArrayBuffer && bytes.byteOffset === 0 && bytes.byteLength === bytes.buffer.byteLength ? bytes.buffer : bytes.slice().buffer;
    }
    return new Promise((resolve, reject) => {
      const job = { id: ++sequence, type, options, source, signal, resolve, reject };
      job.abort = () => {
        if (active === job) { active = undefined; finish(job, aborted()); restart(); }
        else { const position = queue.indexOf(job); if (position >= 0) queue.splice(position, 1); finish(job, aborted()); }
      };
      signal?.addEventListener("abort", job.abort, { once: true });
      queue.push(job); dispatch();
    });
  }
  return {
    report(input, options) { return submit("report", input, options); },
    source(input, options) { return submit("source", input, options); },
    dispose() {
      disposed = true;
      worker?.terminate();
      if (active) { finish(active, aborted()); active = undefined; }
      for (const job of queue.splice(0)) finish(job, aborted());
    },
  };
}
