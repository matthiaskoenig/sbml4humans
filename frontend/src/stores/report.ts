import { defineStore } from "pinia";
import { computed, markRaw, ref, shallowRef } from "vue";

import {
  type ApiError,
  getExample,
  getLocal,
  getUrl,
  postContent,
  postFile,
  toApiError,
} from "@/api/client";
import type { ReportResponse } from "@/api/types";
import { ReportIndex } from "@/report/index";

/** `local` is the report of a file of this machine, which `sbml4humans.show` of the python
 * package created on its local server and which the page reads by its token. */
export type SourceKind = "example" | "url" | "file" | "content" | "local";

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

function sameSource(a: ReportSource, b: ReportSource): boolean {
  if (a.kind !== b.kind) return false;
  if (a.kind === "example") return a.id === b.id;
  if (a.kind === "url") return a.url === b.url;
  if (a.kind === "local") return a.token === b.token;
  return false;
}

export const useReportStore = defineStore("report", () => {
  const response = shallowRef<ReportResponse | null>(null);
  const source = ref<ReportSource | null>(null);
  const loading = ref(false);
  const error = ref<ApiError | null>(null);
  const indexes = shallowRef<Map<string, ReportIndex>>(new Map());

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

  async function load(next: ReportSource, request: () => Promise<ReportResponse>): Promise<void> {
    if (response.value && source.value && sameSource(source.value, next)) return;
    loading.value = true;
    error.value = null;
    response.value = null;
    indexes.value = new Map();
    source.value = next;
    try {
      const result = await request();
      const connected = ReportIndex.forEntries(result.reports);
      for (const index of connected.values()) markRaw(index);
      indexes.value = connected;
      response.value = result;
    } catch (caught) {
      error.value = toApiError(caught);
    } finally {
      loading.value = false;
    }
  }

  const loadExample = (id: string) => load({ kind: "example", id, name: id }, () => getExample(id));
  const loadUrl = (url: string) => load({ kind: "url", url, name: url }, () => getUrl(url));
  const loadLocal = (token: string) =>
    load({ kind: "local", token, name: "local report" }, () => getLocal(token));
  const loadFile = (file: File) => load({ kind: "file", name: file.name }, () => postFile(file));
  const loadContent = (text: string) =>
    load({ kind: "content", name: "pasted SBML" }, () => postContent(text));

  function clear(): void {
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
    loadExample,
    loadUrl,
    loadLocal,
    loadFile,
    loadContent,
    clear,
  };
});
