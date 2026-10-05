import { createPinia, setActivePinia } from "pinia";
import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { useReportStore } from "@/stores/report";

import { loadFixture, loadValidationFixture } from "./fixtures";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return {
    ...original,
    getExample: vi.fn(),
    getUrl: vi.fn(),
    getLocal: vi.fn(),
    getUpload: vi.fn(),
    postFile: vi.fn(),
    postContent: vi.fn(),
    getExampleValidation: vi.fn(),
    getUrlValidation: vi.fn(),
    getLocalValidation: vi.fn(),
    getUploadValidation: vi.fn(),
    postFileValidation: vi.fn(),
    postContentValidation: vi.fn(),
  };
});

/** A promise and the functions which settle it, for a request answered when a test says so. */
function deferred<T>(): {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason: unknown) => void;
} {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("report store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.resetAllMocks();
    // a validation which never answers unless a test answers it
    for (const request of [
      client.getExampleValidation,
      client.getUrlValidation,
      client.getLocalValidation,
      client.getUploadValidation,
      client.postFileValidation,
      client.postContentValidation,
    ]) {
      vi.mocked(request).mockReturnValue(new Promise(() => {}));
    }
  });

  it("loads an example and builds the indexes", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("comp_models"));
    const store = useReportStore();
    await store.loadExample("CompModels");
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    // the archive lists its entries in the order of its manifest, which is the order the
    // fixture was recorded in, so the set is compared and not the order
    expect([...store.entries].sort()).toEqual([
      "./models/omex_comp.xml",
      "./models/omex_comp_flat.xml",
      "./models/omex_minimal.xml",
    ]);
    expect(store.defaultEntry).toBe(store.entries[0]);
    expect(store.indexFor("./models/omex_comp.xml")?.mainModel?.id).toBe("omex_comp");
    expect(store.source).toEqual({ kind: "example", id: "CompModels", name: "CompModels" });
  });

  it("keeps the report of the newer of two loads whose answers arrive in reverse order", async () => {
    const first = deferred<ReturnType<typeof loadFixture>>();
    const second = deferred<ReturnType<typeof loadFixture>>();
    vi.mocked(client.getExample)
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    const store = useReportStore();
    const older = store.loadExample("validation");
    const newer = store.loadExample("BIOMD0000000012");
    second.resolve(loadFixture("repressilator"));
    await newer;
    expect(store.source?.id).toBe("BIOMD0000000012");
    expect(store.loading).toBe(false);
    first.resolve(loadFixture("validation"));
    await older;
    expect(store.source?.id).toBe("BIOMD0000000012");
    expect(store.entries).toEqual(["./BIOMD0000000012_url.xml"]);
    expect(store.indexFor("./validation.xml")).toBeNull();
    expect(store.loading).toBe(false);
    // the validation is requested for the newer report alone
    expect(client.getExampleValidation).toHaveBeenCalledTimes(1);
    expect(vi.mocked(client.getExampleValidation).mock.calls[0]![0]).toBe("BIOMD0000000012");
  });

  it("loads the report of an upload once", async () => {
    vi.mocked(client.getUpload).mockResolvedValue(loadFixture("comp_deletion"));
    const store = useReportStore();
    await store.loadUpload("upload1");
    await store.loadUpload("upload1");
    expect(client.getUpload).toHaveBeenCalledTimes(1);
    expect(client.getUpload).toHaveBeenCalledWith("upload1");
    expect(store.source).toEqual({ kind: "upload", id: "upload1", name: "uploaded model" });
  });

  it("loads the report of a local token once", async () => {
    vi.mocked(client.getLocal).mockResolvedValue(loadFixture("comp_deletion"));
    const store = useReportStore();
    await store.loadLocal("token1");
    await store.loadLocal("token1");
    expect(client.getLocal).toHaveBeenCalledTimes(1);
    expect(client.getLocal).toHaveBeenCalledWith("token1");
    expect(store.source).toEqual({ kind: "local", token: "token1", name: "local report" });
    expect(store.defaultEntry).toBe("./comp_deletion.xml");
    await store.loadLocal("token2");
    expect(client.getLocal).toHaveBeenCalledTimes(2);
  });

  it("prefers the master entry", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    expect(store.defaultEntry).toBe("./BIOMD0000000012_url.xml");
  });

  it("does not reload the loaded example", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    await store.loadExample("BIOMD0000000012");
    expect(client.getExample).toHaveBeenCalledTimes(1);
    await store.loadExample("BIOMD0000000001");
    expect(client.getExample).toHaveBeenCalledTimes(2);
  });

  it("stores the api error", async () => {
    vi.mocked(client.getExample).mockRejectedValue(
      new client.ApiError("example for id does not exist 'x'"),
    );
    const store = useReportStore();
    await store.loadExample("x");
    expect(store.response).toBeNull();
    expect(store.error?.message).toBe("example for id does not exist 'x'");
    expect(store.loading).toBe(false);
  });

  describe("the validation", () => {
    it("is requested with the same source once the report has loaded", async () => {
      const report = deferred<ReturnType<typeof loadFixture>>();
      const validation = deferred<ReturnType<typeof loadValidationFixture>>();
      vi.mocked(client.getExample).mockReturnValue(report.promise);
      vi.mocked(client.getExampleValidation).mockReturnValue(validation.promise);
      const store = useReportStore();
      const loading = store.loadExample("validation");
      expect(client.getExampleValidation).not.toHaveBeenCalled();
      expect(store.validationState).toBeNull();
      report.resolve(loadFixture("validation"));
      await loading;
      expect(client.getExampleValidation).toHaveBeenCalledTimes(1);
      expect(vi.mocked(client.getExampleValidation).mock.calls[0]![0]).toBe("validation");
      expect(vi.mocked(client.getExampleValidation).mock.calls[0]![1]).toBeInstanceOf(AbortSignal);
      expect(store.validationState).toBe("pending");
      expect(store.validationFor("./validation.xml")).toBeNull();
      validation.resolve(loadValidationFixture("validation"));
      await flushPromises();
      expect(store.validationState).toBe("done");
      const index = store.validationFor("./validation.xml");
      expect(index?.issueCounts.error).toBe(1);
      expect(index?.skipped).toBeNull();
      expect(index?.report).toBe(store.indexFor("./validation.xml"));
      expect(store.validationFor("./other.xml")).toBeNull();
    });

    it("resends a file and a pasted content for their validation", async () => {
      vi.mocked(client.postFile).mockResolvedValue(loadFixture("validation"));
      vi.mocked(client.postContent).mockResolvedValue(loadFixture("validation"));
      const store = useReportStore();
      const file = new File(["<sbml/>"], "model.xml");
      await store.loadFile(file);
      expect(vi.mocked(client.postFileValidation).mock.calls[0]![0]).toBe(file);
      await store.loadContent("<sbml/>");
      expect(vi.mocked(client.postContentValidation).mock.calls[0]![0]).toBe("<sbml/>");
    });

    it("is requested for every source kind", async () => {
      vi.mocked(client.getUrl).mockResolvedValue(loadFixture("validation"));
      vi.mocked(client.getLocal).mockResolvedValue(loadFixture("validation"));
      vi.mocked(client.getUpload).mockResolvedValue(loadFixture("validation"));
      const store = useReportStore();
      await store.loadUrl("https://example.org/m.xml");
      expect(vi.mocked(client.getUrlValidation).mock.calls[0]![0]).toBe(
        "https://example.org/m.xml",
      );
      await store.loadLocal("token1");
      expect(vi.mocked(client.getLocalValidation).mock.calls[0]![0]).toBe("token1");
      await store.loadUpload("upload1");
      expect(vi.mocked(client.getUploadValidation).mock.calls[0]![0]).toBe("upload1");
    });

    it("is not requested for a report which failed", async () => {
      vi.mocked(client.getExample).mockRejectedValue(new client.ApiError("no such example"));
      const store = useReportStore();
      await store.loadExample("x");
      expect(client.getExampleValidation).not.toHaveBeenCalled();
      expect(store.validationState).toBeNull();
    });

    it("is aborted by a newer load, whose validation alone is kept", async () => {
      const first = deferred<ReturnType<typeof loadValidationFixture>>();
      const second = deferred<ReturnType<typeof loadValidationFixture>>();
      vi.mocked(client.getExample).mockImplementation((id) =>
        Promise.resolve(loadFixture(id === "validation" ? "validation" : "repressilator")),
      );
      vi.mocked(client.getExampleValidation)
        .mockReturnValueOnce(first.promise)
        .mockReturnValueOnce(second.promise);
      const store = useReportStore();
      await store.loadExample("validation");
      const signal = vi.mocked(client.getExampleValidation).mock.calls[0]![1]!;
      expect(signal.aborted).toBe(false);
      await store.loadExample("BIOMD0000000012");
      expect(signal.aborted).toBe(true);
      expect(store.validationState).toBe("pending");
      // the request of the older report answers late, an aborted fetch rejects
      first.reject(new DOMException("aborted", "AbortError"));
      await flushPromises();
      expect(store.validationState).toBe("pending");
      expect(store.validationError).toBeNull();
      second.resolve(loadValidationFixture("repressilator"));
      await flushPromises();
      expect(store.validationState).toBe("done");
      expect(store.validationFor("./BIOMD0000000012_url.xml")?.issueCounts.warning).toBeGreaterThan(
        0,
      );
    });

    it("ignores the answer of a validation a newer load made obsolete", async () => {
      const first = deferred<ReturnType<typeof loadValidationFixture>>();
      vi.mocked(client.getExample).mockImplementation((id) =>
        Promise.resolve(loadFixture(id === "validation" ? "validation" : "repressilator")),
      );
      vi.mocked(client.getExampleValidation).mockReturnValueOnce(first.promise);
      const store = useReportStore();
      await store.loadExample("validation");
      await store.loadExample("BIOMD0000000012");
      first.resolve(loadValidationFixture("validation"));
      await flushPromises();
      expect(store.validationState).toBe("pending");
      expect(store.validationFor("./validation.xml")).toBeNull();
    });

    it("is aborted by a report load which fails and by clearing the report", async () => {
      vi.mocked(client.getExample)
        .mockResolvedValueOnce(loadFixture("validation"))
        .mockRejectedValueOnce(new client.ApiError("no such example"))
        .mockResolvedValueOnce(loadFixture("validation"));
      const store = useReportStore();
      await store.loadExample("validation");
      const first = vi.mocked(client.getExampleValidation).mock.calls[0]![1]!;
      await store.loadExample("x");
      expect(first.aborted).toBe(true);
      expect(store.validationState).toBeNull();
      await store.loadExample("validation");
      const second = vi.mocked(client.getExampleValidation).mock.calls[1]![1]!;
      store.clear();
      expect(second.aborted).toBe(true);
      expect(store.validationState).toBeNull();
    });

    it("keeps the error of a failed validation", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("validation"));
      vi.mocked(client.getExampleValidation).mockRejectedValue(
        new client.ApiError("the validation failed"),
      );
      const store = useReportStore();
      await store.loadExample("validation");
      await flushPromises();
      expect(store.validationState).toBe("failed");
      expect(store.validationError?.message).toBe("the validation failed");
      expect(store.validationFor("./validation.xml")).toBeNull();
      // the report stays
      expect(store.error).toBeNull();
      expect(store.indexFor("./validation.xml")).not.toBeNull();
    });

    it("gives an entry the server did not reach the reason of the response", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("comp_models"));
      vi.mocked(client.getExampleValidation).mockResolvedValue({
        entries: {
          "./models/omex_comp.xml": {
            issues: loadValidationFixture("validation").entries["./validation.xml"]!.issues,
            skipped: null,
          },
        },
        skipped: "timeout",
      });
      const store = useReportStore();
      await store.loadExample("CompModels");
      await flushPromises();
      expect(store.validationState).toBe("done");
      expect(store.validationFor("./models/omex_comp.xml")?.skipped).toBeNull();
      expect(store.validationFor("./models/omex_comp.xml")?.issueCounts.error).toBe(1);
      expect(store.validationFor("./models/omex_minimal.xml")?.skipped).toBe("timeout");
      expect(store.validationFor("./models/omex_minimal.xml")?.issues).toEqual([]);
    });

    it("marks every entry busy when the server had no room for the validation", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("fan_out"));
      vi.mocked(client.getExampleValidation).mockResolvedValue({ entries: {}, skipped: "busy" });
      const store = useReportStore();
      await store.loadExample("fan_out");
      await flushPromises();
      expect(store.validationFor("./model.xml")?.skipped).toBe("busy");
    });

    it("marks every entry busy when the proxy refuses the validation for its rate limit", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("comp_models"));
      vi.mocked(client.getExampleValidation).mockRejectedValue(
        new client.ApiError(
          "The server answered with status 429: too many requests",
          null,
          [],
          429,
        ),
      );
      const store = useReportStore();
      await store.loadExample("CompModels");
      await flushPromises();
      expect(store.validationState).toBe("done");
      expect(store.validationError).toBeNull();
      for (const location of store.entries) {
        expect(store.validationFor(location)?.skipped).toBe("busy");
        expect(store.validationFor(location)?.issues).toEqual([]);
        expect(store.validationFor(location)?.reloadable).toBe(true);
      }
    });

    it("keeps any other status of a refused validation as its failure", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("validation"));
      vi.mocked(client.getExampleValidation).mockRejectedValue(
        new client.ApiError("The backend answered with status 502", null, [], 502),
      );
      const store = useReportStore();
      await store.loadExample("validation");
      await flushPromises();
      expect(store.validationState).toBe("failed");
      expect(store.validationError?.status).toBe(502);
    });

    it("does not read an entry the answer leaves out without a reason as valid", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("comp_models"));
      vi.mocked(client.getExampleValidation).mockResolvedValue({
        entries: { "./models/omex_comp.xml": { issues: [], skipped: null } },
        skipped: null,
      });
      const store = useReportStore();
      await store.loadExample("CompModels");
      await flushPromises();
      expect(store.validationState).toBe("done");
      expect(store.validationFor("./models/omex_comp.xml")?.skipped).toBeNull();
      expect(store.validationFor("./models/omex_minimal.xml")?.skipped).toBe("unanswered");
      expect(store.validationFor("./models/omex_comp_flat.xml")?.skipped).toBe("unanswered");
    });

    it("knows whether a reload asks for the validation again", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("fan_out"));
      vi.mocked(client.postContent).mockResolvedValue(loadFixture("fan_out"));
      vi.mocked(client.postFile).mockResolvedValue(loadFixture("fan_out"));
      const busy = { entries: {}, skipped: "busy" as const };
      vi.mocked(client.getExampleValidation).mockResolvedValue(busy);
      vi.mocked(client.postContentValidation).mockResolvedValue(busy);
      vi.mocked(client.postFileValidation).mockResolvedValue(busy);
      const store = useReportStore();
      await store.loadExample("fan_out");
      await flushPromises();
      expect(store.validationFor("./model.xml")?.reloadable).toBe(true);
      await store.loadContent("<sbml/>");
      await flushPromises();
      expect(store.validationFor("./model.xml")?.reloadable).toBe(false);
      await store.loadFile(new File(["<sbml/>"], "model.xml"));
      await flushPromises();
      expect(store.validationFor("./model.xml")?.reloadable).toBe(false);
    });

    it("keeps an entry the budget skipped", async () => {
      vi.mocked(client.getExample).mockResolvedValue(loadFixture("fan_out"));
      vi.mocked(client.getExampleValidation).mockResolvedValue(loadValidationFixture("fan_out"));
      const store = useReportStore();
      await store.loadExample("fan_out");
      await flushPromises();
      expect(store.validationFor("./model.xml")?.skipped).toBe("expandedSize");
    });
  });
});
