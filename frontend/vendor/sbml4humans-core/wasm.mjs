/** Load the import-free module in browsers, Node, or an existing worker. */
export async function compileReader(source = new URL("./runtime/sbml4humans-core.wasm", import.meta.url)) {
  if (source instanceof WebAssembly.Module) return source;
  let bytes;
  if (source instanceof URL && source.protocol === "file:") {
    const nodeFs = "node:fs/promises";
    bytes = await (await import(/* @vite-ignore */ nodeFs)).readFile(source);
  } else if (source instanceof URL || typeof source === "string") {
    const response = await fetch(source);
    if (!response.ok) throw new Error(`Could not load the SBML parser: HTTP ${response.status}.`);
    bytes = await response.arrayBuffer();
  } else {
    bytes = source;
  }
  const module = await WebAssembly.compile(bytes);
  if (WebAssembly.Module.imports(module).length) throw new Error("The SBML parser must have no imports.");
  return module;
}

/** Instantiate a parser for use on the current thread, normally inside a worker. */
export async function instantiateReader(source) {
  const module = await compileReader(source);
  const instance = await WebAssembly.instantiate(module, {});
  const api = instance.exports;
  for (const name of ["report_alloc", "report_build", "report_source_build", "report_output_ptr", "report_output_len", "report_release"]) {
    if (typeof api[name] !== "function") throw new Error(`The SBML parser is missing ${name}.`);
  }
  if (typeof api.report_abi_version !== "function" || api.report_abi_version() !== 1) throw new Error("Unsupported SBML parser ABI version.");
  if (!(api.memory instanceof WebAssembly.Memory)) throw new Error("The SBML parser has no exported memory.");
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();
  function output() {
    return JSON.parse(decoder.decode(new Uint8Array(api.memory.buffer, api.report_output_ptr() >>> 0, api.report_output_len() >>> 0)));
  }
  function run(source, options) {
    const bytes = typeof source === "string" ? encoder.encode(source) : source instanceof ArrayBuffer ? new Uint8Array(source) : new Uint8Array(source.buffer, source.byteOffset, source.byteLength);
    const settings = options === undefined ? new Uint8Array() : encoder.encode(JSON.stringify(options));
    const pointer = api.report_alloc(bytes.byteLength + settings.byteLength) >>> 0;
    if (!pointer && bytes.byteLength + settings.byteLength) throw Object.assign(new Error(output().message), output());
    new Uint8Array(api.memory.buffer, pointer, settings.byteLength).set(settings);
    new Uint8Array(api.memory.buffer, pointer + settings.byteLength, bytes.byteLength).set(bytes);
    const status = options === undefined ? api.report_build() : api.report_source_build(settings.byteLength);
    const result = output();
    if (status !== 0) throw Object.assign(new Error(result.message), result);
    return result;
  }
  return {
    report(source) { return run(source); },
    source(source, options = {}) {
      const start = performance.now();
      const uid = options.uid ?? globalThis.crypto?.randomUUID?.().replaceAll("-", "") ?? "";
      const result = run(source, { ...options, uid });
      const elapsed = `${((performance.now() - start) / 1000).toFixed(3)} [s]`;
      for (const entry of Object.values(result.reports)) entry.debug.jsonReportTime = elapsed;
      return result;
    },
    release() { api.report_release(); },
  };
}
