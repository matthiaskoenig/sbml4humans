import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { useReportStore } from "@/stores/report";

import { loadFixture } from "./fixtures";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return { ...original, getExample: vi.fn(), getUrl: vi.fn() };
});

describe("report store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.mocked(client.getExample).mockReset();
  });

  it("loads an example and builds the indexes", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("comp_models"));
    const store = useReportStore();
    await store.loadExample("CompModels");
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    expect(store.entries).toEqual([
      "./models/omex_comp_flat.xml",
      "./models/omex_minimal.xml",
      "./models/omex_comp.xml",
    ]);
    expect(store.defaultEntry).toBe("./models/omex_comp_flat.xml");
    expect(store.indexFor("./models/omex_comp.xml")?.mainModel?.id).toBe("omex_comp");
    expect(store.source).toEqual({ kind: "example", id: "CompModels", name: "CompModels" });
  });

  it("prefers the master entry", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    expect(store.defaultEntry).toBe("./model.xml");
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
});
