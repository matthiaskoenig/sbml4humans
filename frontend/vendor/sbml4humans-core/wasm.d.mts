import type { Report, ReportResponse } from "./report.js";
import type { Input, WasmSource, SourceOptions } from "./index.mjs";
export interface SynchronousReader {
  report(source: Input): Report;
  source(source: Input, options?: Omit<SourceOptions, "signal" | "transfer">): ReportResponse;
  release(): void;
}
export function compileReader(source?: WasmSource): Promise<WebAssembly.Module>;
export function instantiateReader(source?: WasmSource): Promise<SynchronousReader>;
