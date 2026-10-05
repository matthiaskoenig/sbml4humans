import { createPinia, setActivePinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { vTooltip } from "@/directives/tooltip";
import ReportPage from "@/pages/ReportPage.vue";
import { router } from "@/router";
import { LOCAL_PING_INTERVAL, useReportStore } from "@/stores/report";

import { loadFixture, loadValidationFixture } from "./fixtures";

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return {
    ...original,
    getExample: vi.fn(),
    postContent: vi.fn(),
    getLocal: vi.fn(),
    pingLocal: vi.fn(),
    getUpload: vi.fn(),
    getExampleValidation: vi.fn(),
    getLocalValidation: vi.fn(),
    getUploadValidation: vi.fn(),
    postContentValidation: vi.fn(),
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
    // a validation which never answers unless a test answers it
    for (const request of [
      client.getExampleValidation,
      client.getLocalValidation,
      client.getUploadValidation,
      client.postContentValidation,
    ]) {
      vi.mocked(request)
        .mockReset()
        .mockReturnValue(new Promise(() => {}));
    }
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

  it("shows the validation of the report once it is answered, pending until then", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("validation"));
    let answer!: (response: ReturnType<typeof loadValidationFixture>) => void;
    vi.mocked(client.getExampleValidation).mockReturnValue(
      new Promise((resolve) => (answer = resolve)),
    );
    await router.push("/examples/validation");
    wrapper = mount(ReportPage, {
      global: { plugins: [router], directives: { tooltip: vTooltip } },
    });
    await flushPromises();
    const page = wrapper;
    expect(page.find("[data-testid=report-page]").exists()).toBe(true);
    expect(page.find("[data-testid=validation-pending]").exists()).toBe(true);
    expect(page.find("[data-testid=validation-errors]").exists()).toBe(false);
    expect(page.find("[data-testid=bar-issue-model]").exists()).toBe(false);
    answer(loadValidationFixture("validation"));
    await flushPromises();
    expect(page.find("[data-testid=validation-pending]").exists()).toBe(false);
    expect(page.get("[data-testid=validation-errors]").text()).toBe("1 error");
    expect(page.find("[data-testid=bar-issue-model]").exists()).toBe(true);
    expect(page.find("[data-testid=row-issue]").exists()).toBe(true);
  });

  it("leads from a failed validation to its details in the inspector of the document", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("validation"));
    vi.mocked(client.getExampleValidation).mockRejectedValue(
      new client.ApiError("the validation failed", "Traceback (most recent call last)"),
    );
    await router.push("/examples/validation");
    wrapper = mount(ReportPage, {
      global: { plugins: [router], directives: { tooltip: vTooltip } },
    });
    await flushPromises();
    const page = wrapper;
    await page.get("[data-testid=validation-failed]").trigger("click");
    await flushPromises();
    const failure = page.get("[data-testid=validation-failure]");
    expect(failure.text()).toContain("the validation failed");
    await failure.get("[data-testid=validation-failure-toggle]").trigger("click");
    expect(failure.get("[data-testid=validation-failure-traceback]").text()).toBe(
      "Traceback (most recent call last)",
    );
  });

  it("shows the empty state on /report with an empty url", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    const page = await mountReport({ url: "" });
    expect(page.find("[data-testid=no-report]").exists()).toBe(true);
    expect(page.find("[data-testid=report-page]").exists()).toBe(false);
  });

  it("shows the report of an upload", async () => {
    vi.mocked(client.getUpload).mockReset().mockResolvedValue(loadFixture("repressilator"));
    const page = await mountReport({ upload: "upload1" });
    expect(client.getUpload).toHaveBeenCalledWith("upload1");
    expect(page.find("[data-testid=report-page]").exists()).toBe(true);
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
    // the inspector and the tables are the two panes of one horizontal split, the tables first
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

  it("opens with the model in the inspector, which a reader can close", async () => {
    vi.mocked(client.postContent).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadContent("<sbml/>");
    const model = store.indexFor(store.defaultEntry!)!.mainModel!;
    const page = await mountReport();

    expect(router.currentRoute.value.query.pk).toBe(model.pk);
    expect(page.get("[data-testid=inspector-type]").text()).toBe("Model");
    // the selection replaced the route the report was opened with, the way back leaves the report
    expect((window.history.state as { replaced: boolean }).replaced).toBe(true);

    await page.get("[data-testid=inspector-close]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBeUndefined();
    expect(page.find("[data-testid=inspector]").exists()).toBe(false);
  });

  it("links the list of a table from its heading where the list states something", async () => {
    vi.mocked(client.postContent).mockResolvedValue(loadFixture("list_of"));
    const store = useReportStore();
    await store.loadContent("<sbml/>");
    const index = store.indexFor(store.defaultEntry!)!;
    const page = await mountReport();

    const link = (type: string) =>
      page.find(`[data-testid=section-${type}] [data-testid=section-list] a`);
    expect(link("Species").text()).toBe("metabolites");
    expect(link("Species").attributes("data-pk")).toBe(
      index.list(index.mainModel!.pk, "listOfSpecies")!.pk,
    );
    // a list without an id is named by the name it has in the file
    expect(link("UnitDefinition").text()).toBe("listOfUnitDefinitions");
    // the list of the compartments states nothing, and is no element of the report
    expect(page.find("[data-testid=section-Compartment] h2").exists()).toBe(true);
    expect(link("Compartment").exists()).toBe(false);

    // the link selects the list like every link to an element
    await link("Species").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(link("Species").attributes("data-pk"));
    expect(page.get("[data-testid=inspector-type]").text()).toBe("ListOf");
  });

  it("keeps the element a url names", async () => {
    vi.mocked(client.postContent).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadContent("<sbml/>");
    const index = store.indexFor(store.defaultEntry!)!;
    const species = index.byType(index.mainModel!.id!).get("Species")![0]!;
    const page = await mountReport({ pk: species.pk });

    expect(router.currentRoute.value.query.pk).toBe(species.pk);
    expect(page.get("[data-testid=inspector-type]").text()).toBe("Species");
  });

  it("selects nothing on a route which shows no report", async () => {
    vi.mocked(client.getExample).mockResolvedValue(loadFixture("repressilator"));
    const store = useReportStore();
    await store.loadExample("BIOMD0000000012");
    await mountReport();
    expect(router.currentRoute.value.query.pk).toBeUndefined();
  });
});
