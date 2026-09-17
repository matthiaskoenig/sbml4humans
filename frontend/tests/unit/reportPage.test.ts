import PrimeVue from "primevue/config";
import { createPinia, setActivePinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { primevueOptions } from "@/assets/primevue";
import { vTooltip } from "@/directives/tooltip";
import ReportPage from "@/pages/ReportPage.vue";
import { router } from "@/router";
import { useReportStore } from "@/stores/report";

import { loadFixture } from "./fixtures";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return { ...original, getExample: vi.fn(), postContent: vi.fn() };
});

// jsdom has no ResizeObserver, which the PrimeVue virtual scroller observes the table with
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
globalThis.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;

let wrapper: ReturnType<typeof mount> | null = null;

async function mountReport(query: Record<string, string> = {}) {
  await router.push({ path: "/report", query });
  await router.isReady();
  wrapper = mount(ReportPage, {
    global: {
      plugins: [router, [PrimeVue, primevueOptions]],
      directives: { tooltip: vTooltip },
    },
  });
  await flushPromises();
  return wrapper;
}

describe("ReportPage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.mocked(client.getExample).mockReset();
    vi.mocked(client.postContent).mockReset();
  });

  afterEach(() => {
    wrapper?.unmount();
    wrapper = null;
  });

  it("shows the empty state on /report while the report of an example is loaded", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    expect(store.response).not.toBeNull();
    const page = await mountReport();
    expect(page.find("[data-testid=no-report]").exists()).toBe(true);
    expect(page.find("[data-testid=report-page]").exists()).toBe(false);
  });

  it("shows the empty state on /report with an empty url", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    const page = await mountReport({ url: "" });
    expect(page.find("[data-testid=no-report]").exists()).toBe(true);
    expect(page.find("[data-testid=report-page]").exists()).toBe(false);
  });

  it("shows the report of pasted content on /report", async () => {
    vi.mocked(client.postContent).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadContent("<sbml/>");
    const page = await mountReport();
    expect(page.find("[data-testid=report-page]").exists()).toBe(true);
    expect(page.find("[data-testid=no-report]").exists()).toBe(false);
  });
});
