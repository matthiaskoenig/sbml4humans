import { defineStore } from "pinia";
import { computed, markRaw, ref, shallowRef } from "vue";

import {
  ApiError,
  getExample,
  getExampleOde,
  getExampleValidation,
  getLocal,
  getLocalOde,
  getLocalValidation,
  getUpload,
  getUploadOde,
  getUploadValidation,
  getUrl,
  getUrlOde,
  getUrlValidation,
  type OdeDownloadFile,
  type OdeFormat,
  postContent,
  postContentOde,
  postContentValidation,
  postFile,
  postFileOde,
  postFileValidation,
  toApiError,
  TOO_MANY_REQUESTS,
} from "@/api/client";
import type { ReportResponse, ValidationResponse } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { ValidationIndex } from "@/report/validationIndex";

/** The download of the differential equations of a report in a format, see `odeCode`. */
type OdeDownload = (format: OdeFormat, location: string) => Promise<OdeDownloadFile>;

/** The differential equations of an entry in a format of sbmlode: the code or the document and
 * the name of its file. */
export interface OdeCode {
  filename: string;
  text: string;
}

/** `local` is the report of a file of this machine, which `sbml4humans.show` of the python
 * package created on its local server and which the page reads by its token. `upload` is the
 * report of a model another tool uploaded, which the backend keeps for 24 hours under its id. */
export type SourceKind = "example" | "url" | "file" | "content" | "local" | "upload";

/** How often an open local report tells its server that it is still read [ms]. The server ends
 * itself after a quarter of an hour without a request, and a browser wakes the timers of a tab
 * in the background once a minute. */
export const LOCAL_PING_INTERVAL = 60_000;

/** Where the current report came from. */
export interface ReportSource {
  kind: SourceKind;
  id?: string;
  url?: string;
  token?: string;
  /** Shown while loading and in the context bar. */
  name: string;
}

/** The validation of the report shown: requested once the report has loaded, `pending` until it
 * is answered, `done` with a `ValidationIndex` for every entry, `failed` with its error; null
 * without a report. */
export type ValidationState = "pending" | "done" | "failed";

function sameSource(a: ReportSource, b: ReportSource): boolean {
  if (a.kind !== b.kind) return false;
  if (a.kind === "example") return a.id === b.id;
  if (a.kind === "url") return a.url === b.url;
  if (a.kind === "local") return a.token === b.token;
  if (a.kind === "upload") return a.id === b.id;
  return false;
}

export const useReportStore = defineStore("report", () => {
  const response = shallowRef<ReportResponse | null>(null);
  const source = ref<ReportSource | null>(null);
  const loading = ref(false);
  const error = ref<ApiError | null>(null);
  const indexes = shallowRef<Map<string, ReportIndex>>(new Map());
  const validationState = ref<ValidationState | null>(null);
  const validationError = ref<ApiError | null>(null);
  const validations = shallowRef<Map<string, ValidationIndex>>(new Map());
  /** The load which is current: a load which a newer one followed drops its answers. */
  let generation = 0;
  /** Aborts the validation request of the current report. */
  let validationController: AbortController | null = null;

  /** The manifest locations of the SBML entries with a report. */
  const entries = computed(() => (response.value ? Object.keys(response.value.reports) : []));

  /** The master entry if it has a report, else the first entry. */
  const defaultEntry = computed<string | null>(() => {
    const master = response.value?.manifest.entries?.find(
      (entry) => entry.master && entries.value.includes(entry.location),
    );
    return master?.location ?? entries.value[0] ?? null;
  });

  function indexFor(location: string): ReportIndex | null {
    return indexes.value.get(location) ?? null;
  }

  /** The validation of an entry, null while it is pending, after it failed and without a report. */
  function validationFor(location: string): ValidationIndex | null {
    return validations.value.get(location) ?? null;
  }

  function resetValidation(): void {
    validationController?.abort();
    validationController = null;
    validationState.value = null;
    validationError.value = null;
    validations.value = new Map();
  }

  /** Request the validation of the report which has just loaded, with the same source. An entry
   * the answer leaves out was not reached and takes the reason of the answer; one the answer
   * leaves out without a reason is `unanswered`, never a valid document. A request the proxy
   * refuses for the rate limit of the client (429) is answered as `busy`, like the backend which
   * has no room for it: the reader tries again later. */
  async function validate(
    reports: Map<string, ReportIndex>,
    request: (signal: AbortSignal) => Promise<ValidationResponse>,
    reloadable: boolean,
  ): Promise<void> {
    const controller = new AbortController();
    validationController = controller;
    validationState.value = "pending";
    try {
      let result: ValidationResponse;
      try {
        result = await request(controller.signal);
      } catch (caught) {
        if (!(caught instanceof ApiError) || caught.status !== TOO_MANY_REQUESTS) throw caught;
        result = { entries: {}, skipped: "busy" };
      }
      if (controller.signal.aborted) return;
      const next = new Map<string, ValidationIndex>();
      for (const [location, report] of reports) {
        const entry = result.entries[location] ?? {
          issues: [],
          skipped: result.skipped ?? "unanswered",
        };
        next.set(location, markRaw(new ValidationIndex(report, entry, reloadable)));
      }
      validations.value = next;
      validationState.value = "done";
    } catch (caught) {
      // an aborted request rejects as well, its report is gone
      if (controller.signal.aborted) return;
      validationError.value = toApiError(caught);
      validationState.value = "failed";
    } finally {
      if (validationController === controller) validationController = null;
    }
  }

  /** The download of the differential equations of the source of the report, null without one:
   * a file and pasted content are sent again like for the validation. */
  let download: OdeDownload | null = null;

  /** The code of each entry and format which was asked for, a promise each; a failed one is
   * dropped, so that the next view asks again. */
  let codes = new Map<string, Promise<OdeCode>>();

  /** The differential equations of an entry of the report in a format of sbmlode, the code and
   * the name of its file, fetched once per report. */
  function odeCode(format: OdeFormat, location: string): Promise<OdeCode> {
    const request = download;
    if (request === null) return Promise.reject(new ApiError("No report is loaded"));
    const key = `${location}\n${format}`;
    let code = codes.get(key);
    if (code === undefined) {
      const current = codes;
      code = request(format, location).then(async (file) => ({
        filename: file.filename,
        text: await file.blob.text(),
      }));
      code.catch(() => {
        if (current.get(key) === code) current.delete(key);
      });
      codes.set(key, code);
    }
    return code;
  }

  async function load(
    next: ReportSource,
    request: () => Promise<ReportResponse>,
    validation: (signal: AbortSignal) => Promise<ValidationResponse>,
    ode: OdeDownload,
  ): Promise<void> {
    if (response.value && source.value && sameSource(source.value, next)) return;
    const current = ++generation;
    download = ode;
    codes = new Map();
    resetValidation();
    loading.value = true;
    error.value = null;
    response.value = null;
    indexes.value = new Map();
    source.value = next;
    let connected: Map<string, ReportIndex>;
    try {
      const result = await request();
      if (current !== generation) return;
      connected = ReportIndex.forEntries(result.reports);
      for (const index of connected.values()) markRaw(index);
      indexes.value = connected;
      response.value = result;
    } catch (caught) {
      if (current === generation) error.value = toApiError(caught);
      return;
    } finally {
      if (current === generation) loading.value = false;
    }
    // a file and pasted content are not part of the url of the page, a reload loses them
    void validate(connected, validation, next.kind !== "file" && next.kind !== "content");
  }

  const loadExample = (id: string) =>
    load(
      { kind: "example", id, name: id },
      () => getExample(id),
      (signal) => getExampleValidation(id, signal),
      (format) => getExampleOde(id, format),
    );
  const loadUrl = (url: string) =>
    load(
      { kind: "url", url, name: url },
      () => getUrl(url),
      (signal) => getUrlValidation(url, signal),
      (format, location) => getUrlOde(url, format, location),
    );
  const loadLocal = (token: string) =>
    load(
      { kind: "local", token, name: "local report" },
      () => getLocal(token),
      (signal) => getLocalValidation(token, signal),
      (format, location) => getLocalOde(token, format, location),
    );
  const loadUpload = (id: string) =>
    load(
      { kind: "upload", id, name: "uploaded model" },
      () => getUpload(id),
      (signal) => getUploadValidation(id, signal),
      (format, location) => getUploadOde(id, format, location),
    );
  const loadFile = (file: File) =>
    load(
      { kind: "file", name: file.name },
      () => postFile(file),
      (signal) => postFileValidation(file, signal),
      (format, location) => postFileOde(file, format, location),
    );
  const loadContent = (text: string) =>
    load(
      { kind: "content", name: "pasted SBML" },
      () => postContent(text),
      (signal) => postContentValidation(text, signal),
      (format, location) => postContentOde(text, format, location),
    );

  function clear(): void {
    generation += 1;
    download = null;
    codes = new Map();
    resetValidation();
    loading.value = false;
    response.value = null;
    source.value = null;
    error.value = null;
    indexes.value = new Map();
  }

  return {
    response,
    source,
    loading,
    error,
    entries,
    defaultEntry,
    indexFor,
    validationState,
    validationError,
    validationFor,
    loadExample,
    loadUrl,
    loadLocal,
    loadUpload,
    loadFile,
    loadContent,
    odeCode,
    clear,
  };
});
