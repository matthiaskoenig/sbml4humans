import type { Report, ReportResponse } from "./report.js";
export type { Report } from "./report.js";
export type Input = string | ArrayBuffer | ArrayBufferView;
export type WasmSource = WebAssembly.Module | BufferSource | URL | string;
export interface ReportOptions {
  signal?: AbortSignal;
  /** Transfer a complete ArrayBuffer; the caller relinquishes ownership. */
  transfer?: boolean;
}
export interface Reader {
  report(input: Input, options?: ReportOptions): Promise<Report>;
  source(input: Input, options?: SourceOptions): Promise<ReportResponse>;
  /** Terminate the worker and reject outstanding requests with AbortError. */
  dispose(): void;
}
export interface ReaderOptions {
  source?: WasmSource;
  workerFactory?: () => Worker;
}
/** Create an isolated worker using the import-free Rust WASM report pipeline. */
export function createReader(options?: ReaderOptions): Promise<Reader>;

/** Options apply independently to each complete source request. */
export interface SourceOptions extends ReportOptions {
  uid?: string;
  location?: string;
  maxExpandedElements?: number;
  limits?: {
    maxContentSize?: number;
    maxArchiveEntries?: number;
    maxCompressionRatio?: number;
    compressionRatioMinSize?: number;
  };
}
