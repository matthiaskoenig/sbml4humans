import { instantiateReader } from "./wasm.mjs";

let send;
let listen;
if (typeof globalThis.postMessage === "function") {
  send = (value) => globalThis.postMessage(value);
  listen = (handler) => globalThis.addEventListener("message", (event) => handler(event.data));
} else {
  const nodeWorkers = "node:worker_threads";
  const { parentPort } = await import(/* @vite-ignore */ nodeWorkers);
  send = (value) => parentPort.postMessage(value);
  listen = (handler) => parentPort.on("message", handler);
}
let reader;
listen(async ({ type, module, id, source, options }) => {
  try {
    if (type === "init") { reader = await instantiateReader(module); send({ type: "ready" }); }
    else if (type === "report") { send({ type: "report", id, result: reader.report(source) }); }
    else if (type === "source") { send({ type: "report", id, result: reader.source(source, options) }); }
    else if (type === "release") { reader?.release(); }
  } catch (error) {
    send({ type: "error", id, message: error.message, kind: error.kind ?? "internal", fatal: error instanceof WebAssembly.RuntimeError });
  }
});
