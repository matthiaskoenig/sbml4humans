import { createPinia, setActivePinia } from "pinia";
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { readSource } from "@/parsing/reader";
import HomePage from "@/pages/HomePage.vue";
// The report route lazy-loads this page; importing it here warms the module cache so the
// router's dynamic import resolves within the microtask queue `flushPromises()` flushes,
// instead of needing a real timer tick.
import "@/pages/ReportPage.vue";
import { router } from "@/router";
import { vTooltip } from "@/directives/tooltip";

import { loadFixture } from "./fixtures";

vi.mock("@/parsing/reader", () => ({ readSource: vi.fn() }));

vi.mock("@/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof client>();
  return { ...original, getUrl: vi.fn(), postContent: vi.fn(), postFile: vi.fn() };
});

// jsdom only fires a form's native `submit` event through a submit button's click when the form
// is connected to `document` (HTMLFormElement._doRequestSubmit no-ops otherwise), so the wrapper
// is attached to `document.body` and unmounted again after each test.
let wrapper: ReturnType<typeof mount> | null = null;

async function mountHome() {
  await router.push("/");
  await router.isReady();
  wrapper = mount(HomePage, {
    global: { plugins: [createPinia(), router], directives: { tooltip: vTooltip } },
    attachTo: document.body,
  });
  return wrapper;
}

describe("HomePage", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    vi.mocked(client.getUrl).mockReset();
    vi.mocked(readSource).mockReset();
  });

  afterEach(() => {
    wrapper?.unmount();
    wrapper = null;
  });

  it("navigates to the report route of the url after loading it", async () => {
    vi.mocked(client.getUrl).mockResolvedValue(loadFixture("repressilator"));
    const wrapper = await mountHome();
    await wrapper.get("[data-testid=home-tab-url]").trigger("click");
    await wrapper.get("[data-testid=url-input]").setValue("https://example.org/model.xml");
    await wrapper.get("[data-testid=url-submit]").trigger("click");
    await flushPromises();
    expect(client.getUrl).toHaveBeenCalledWith(
      "https://example.org/model.xml",
      expect.any(AbortSignal),
    );
    expect(router.currentRoute.value.name).toBe("report");
    expect(router.currentRoute.value.query.url).toBe("https://example.org/model.xml");
    expect(localStorage.getItem("sbml4humans.lastUrl")).toBe("https://example.org/model.xml");
  });

  it("shows the logo in the heading", async () => {
    const wrapper = await mountHome();
    const heading = wrapper.get("h1");
    expect(heading.text()).toBe("SBML4Humans");
    // the app bar carries a logo of its own, the heading's is the one inside `h1`
    const logo = heading.get("[data-testid=app-logo]");
    expect(logo.attributes("src")).toContain("logo");
    expect(logo.attributes("alt")).toBeTruthy();
  });

  it("shows the api error inline", async () => {
    vi.mocked(readSource).mockRejectedValue(new client.ApiError("no SBML", "Traceback"));
    const wrapper = await mountHome();
    await wrapper.get("[data-testid=home-tab-paste]").trigger("click");
    await wrapper.get("[data-testid=paste-input]").setValue("<nonsense/>");
    await wrapper.get("[data-testid=paste-submit]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-testid=error-message]").text()).toBe("no SBML");
    expect(router.currentRoute.value.name).toBe("home");
  });
  it("does not navigate after its load finishes following unmount", async () => {
    let resolve!: (value: ReturnType<typeof loadFixture>) => void;
    vi.mocked(readSource).mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    const page = await mountHome();
    await page.get("[data-testid=home-tab-paste]").trigger("click");
    await page.get("[data-testid=paste-input]").setValue("<sbml/>");
    await page.get("[data-testid=paste-submit]").trigger("click");
    page.unmount();
    wrapper = null;
    await router.push("/examples");
    resolve(loadFixture("repressilator"));
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("examples");
  });
});
