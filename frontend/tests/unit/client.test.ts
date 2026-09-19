import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getAnnotationResource,
  getExample,
  getExamples,
  postContent,
  postFile,
} from "@/api/client";

import { loadFixture } from "./fixtures";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("requests the examples from the api url", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ examples: [{ id: "a" }] }));
    vi.stubGlobal("fetch", fetchMock);
    const examples = await getExamples();
    expect(examples).toEqual([{ id: "a" }]);
    expect(fetchMock).toHaveBeenCalledWith(
      `${import.meta.env.VITE_API_URL}/examples`,
      expect.anything(),
    );
  });

  it("encodes the example id", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ uid: "x", manifest: {}, reports: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await getExample("icg_body (icg_body.xml)");
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      `${import.meta.env.VITE_API_URL}/examples/icg_body%20(icg_body.xml)`,
    );
  });

  it("throws ApiError for the error contract", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          errors: ["example for id does not exist 'x'", "Traceback ..."],
          warnings: [],
          info: {},
        }),
      ),
    );
    const error = await getExample("x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toBe("example for id does not exist 'x'");
    expect((error as ApiError).traceback).toBe("Traceback ...");
  });

  it("throws ApiError when the backend is not reachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const error = await getExamples().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toMatch(/not reachable/);
  });

  it("throws ApiError for a non JSON body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>", { status: 502 })));
    const error = await getExamples().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toMatch(/502/);
  });

  it("posts the file as multipart field source", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ uid: "x", manifest: {}, reports: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await postFile(new File(["<sbml/>"], "model.xml"));
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect((init.body as FormData).get("source")).toBeInstanceOf(File);
  });

  it("posts the content as raw body", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ uid: "x", manifest: {}, reports: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await postContent("<sbml/>");
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.method).toBe("POST");
    expect(init.body).toBe("<sbml/>");
  });

  it("returns the annotation info although it carries an errors list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          resource: "https://identifiers.org/chebi/CHEBI:15377",
          label: "water",
          errors: ["no ols"],
          warnings: [],
        }),
      ),
    );
    const info = await getAnnotationResource("https://identifiers.org/chebi/CHEBI:15377");
    expect(info.label).toBe("water");
  });

  it("aborts an annotation resource request after 15 seconds", async () => {
    const timeoutSpy = vi.spyOn(AbortSignal, "timeout");
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse({ resource: "https://identifiers.org/chebi/CHEBI:15377", label: "water" }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await getAnnotationResource("https://identifiers.org/chebi/CHEBI:15377");
    expect(timeoutSpy).toHaveBeenCalledWith(15_000);
    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    expect(init.signal).toBeDefined();
    expect(init.signal).toBe(timeoutSpy.mock.results[0]?.value);
  });

  it("fixtures carry the report response shape", () => {
    const response = loadFixture("repressilator");
    expect(response.manifest.entries?.some((entry) => entry.master)).toBe(true);
    const report = response.reports["./BIOMD0000000012_url.xml"]?.report;
    expect(report?.document.sbmlType).toBe("SBMLDocument");
    expect(report?.models?.[0]?.id).toBe("BIOMD0000000012");
    expect(report?.linkGraph?.edges?.length).toBeGreaterThan(0);
  });
});
