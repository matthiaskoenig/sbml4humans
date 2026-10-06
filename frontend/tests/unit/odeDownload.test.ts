import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  getExampleOde,
  getLocalOde,
  getUploadOde,
  getUrlOde,
  postContentOde,
  postFileOde,
} from "@/api/client";

const API = import.meta.env.VITE_API_URL;

function fileResponse(text: string, filename: string): Response {
  return new Response(text, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}

describe("the downloads of the ODE system", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("requests the format of an example and names the file as the backend does", async () => {
    const fetchMock = vi.fn().mockResolvedValue(fileResponse("def f_dxdt(): ...", "m.py"));
    vi.stubGlobal("fetch", fetchMock);
    const file = await getExampleOde("icg_body (icg_body.xml)", "python");
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      `${API}/ode/examples/icg_body%20(icg_body.xml)?format=python`,
    );
    expect(file.filename).toBe("m.py");
    expect(await file.blob.text()).toBe("def f_dxdt(): ...");
  });

  it("sends the source and the location of every other kind of report", async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(fileResponse("x", "m.md")));
    vi.stubGlobal("fetch", fetchMock);
    await getUrlOde("https://example.org/m.omex", "julia", "./a b.xml");
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      `${API}/ode/url?url=https%3A%2F%2Fexample.org%2Fm.omex&format=julia&location=.%2Fa+b.xml`,
    );
    await getUploadOde("abc", "r", "./m.xml");
    expect(fetchMock.mock.calls[1]?.[0]).toBe(`${API}/ode/upload/abc?format=r&location=.%2Fm.xml`);
    await getLocalOde("tok", "latex", "./m.xml");
    expect(fetchMock.mock.calls[2]?.[0]).toBe(
      `${API}/local/ode/tok?format=latex&location=.%2Fm.xml`,
    );
    await postContentOde("<sbml/>", "markdown", "./model.xml");
    expect(fetchMock.mock.calls[3]?.[0]).toBe(
      `${API}/ode/content?format=markdown&location=.%2Fmodel.xml`,
    );
    expect(fetchMock.mock.calls[3]?.[1]).toMatchObject({ method: "POST", body: "<sbml/>" });
    const model = new File(["<sbml/>"], "m.xml");
    await postFileOde(model, "typst", "./m.xml");
    expect(fetchMock.mock.calls[4]?.[0]).toBe(`${API}/ode/file?format=typst&location=.%2Fm.xml`);
    const body = fetchMock.mock.calls[4]?.[1]?.body as FormData;
    expect(body.get("source")).toBeInstanceOf(File);
  });

  it("throws the error of the error contract", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(
          new Response(
            JSON.stringify({
              errors: ["algebraic rule is not supported"],
              warnings: [],
              info: {},
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
        ),
      ),
    );
    await expect(getExampleOde("x", "python")).rejects.toThrow(ApiError);
    await expect(getExampleOde("x", "python")).rejects.toThrow("algebraic rule");
  });

  it("names a file without a name of its own after the model", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("x", { headers: { "Content-Type": "text/plain" } })),
    );
    expect((await getExampleOde("x", "python")).filename).toBe("model.py");
  });
});
