import { createPinia, setActivePinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { vTooltip } from "@/directives/tooltip";
import ReportPage from "@/pages/ReportPage.vue";
import { router } from "@/router";
import { LOCAL_PING_INTERVAL, useReportStore } from "@/stores/report";

import { loadFixture } from "./fixtures";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return {
    ...original,
    getExample: vi.fn(),
    postContent: vi.fn(),
    getLocal: vi.fn(),
    pingLocal: vi.fn(),
  };
});

let wrapper: ReturnType<typeof mount> | null = null;

async function mountReport(query: Record<string, string> = {}) {
  await router.push({ path: "/report", query });
  await router.isReady();
  wrapper = mount(ReportPage, {
    global: {
      plugins: [router],
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
    vi.useRealTimers();
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

  it("shows the report of a local token and keeps the local server alive while it is open", async () => {
    vi.useFakeTimers();
    vi.mocked(client.getLocal).mockReset().mockResolvedValue(loadFixture("repressilator"));
    vi.mocked(client.pingLocal).mockReset().mockResolvedValue(undefined);
    const page = await mountReport({ local: "token1" });
    expect(client.getLocal).toHaveBeenCalledWith("token1");
    expect(page.find("[data-testid=report-page]").exists()).toBe(true);

    // the server ends itself when it is idle, so an open report says that it is still read
    expect(client.pingLocal).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(LOCAL_PING_INTERVAL);
    expect(client.pingLocal).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(2 * LOCAL_PING_INTERVAL);
    expect(client.pingLocal).toHaveBeenCalledTimes(3);
    page.unmount();
    wrapper = null;
    await vi.advanceTimersByTimeAsync(2 * LOCAL_PING_INTERVAL);
    expect(client.pingLocal).toHaveBeenCalledTimes(3);
  });

  it("does not ping for a report which is not a local one", async () => {
    vi.useFakeTimers();
    vi.mocked(client.pingLocal).mockReset();
    vi.mocked(client.postContent).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadContent("<sbml/>");
    await mountReport();
    await vi.advanceTimersByTimeAsync(3 * LOCAL_PING_INTERVAL);
    expect(client.pingLocal).not.toHaveBeenCalled();
  });

  it("shows the report of pasted content on /report", async () => {
    vi.mocked(client.postContent).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadContent("<sbml/>");
    const page = await mountReport();
    expect(page.find("[data-testid=report-page]").exists()).toBe(true);
    expect(page.find("[data-testid=no-report]").exists()).toBe(false);
  });

  it("opens the inspector at the right of the tables and carries the footer", async () => {
    vi.mocked(client.postContent).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadContent("<sbml/>");
    const pk = store.indexFor(store.defaultEntry!)!.mainModel!.pk;
    const page = await mountReport({ pk });

    const reportPage = page.get("[data-testid=report-page]");
    expect(reportPage.find("[data-testid=type-bar]").exists()).toBe(true);
    // the tables and the inspector are the two panes of one horizontal split, the tables first
    const split = reportPage.get("[data-testid=split-handle]").element.parentElement!;
    expect(split.className).toContain("flex-row");
    const panes = [...split.querySelectorAll("[data-testid=tables], [data-testid=inspector]")].map(
      (pane) => pane.getAttribute("data-testid"),
    );
    expect(panes).toEqual(["tables", "inspector"]);
    // the footer sits under the split, not inside the pane which scrolls with the tables
    const footer = reportPage.get("[data-testid=app-footer]");
    expect(split.contains(footer.element)).toBe(false);
  });
});
