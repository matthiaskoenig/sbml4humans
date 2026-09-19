import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import AppBar from "@/components/layout/AppBar.vue";
import { vTooltip } from "@/directives/tooltip";
import { DOCS_URL } from "@/report/glossary";
import { router } from "@/router";
import { useReportStore } from "@/stores/report";

function mountBar() {
  return mount(AppBar, { global: { plugins: [router], directives: { tooltip: vTooltip } } });
}

describe("AppBar", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("links to the documentation site next to the examples link", () => {
    const wrapper = mountBar();
    const link = wrapper.get("[data-testid=app-bar-docs]");
    expect(link.attributes("href")).toBe(DOCS_URL);
    expect(link.attributes("target")).toBe("_blank");
    expect(link.attributes("rel")).toBe("noopener");
    expect(link.text()).toBe("Documentation");
  });

  it("shows the logo in the link to the home page", () => {
    const wrapper = mountBar();
    const logo = wrapper.get("[data-testid=app-logo]");
    expect(logo.element.tagName).toBe("IMG");
    expect(logo.attributes("src")).toContain("logo");
    expect(logo.attributes("alt")).toBeTruthy();
    // the logo and the wordmark are the same link to the home page
    const home = wrapper.get("a[href='/']");
    expect(home.find("[data-testid=app-logo]").exists()).toBe(true);
    expect(home.text()).toBe("SBML4Humans");
  });

  it("opens an issue of the repository for feedback, which names the report that is shown", async () => {
    const store = useReportStore();
    store.source = { kind: "example", id: "repressilator", name: "repressilator" };
    await router.push("/examples/repressilator?q=laci");
    const link = mountBar().get("[data-testid=app-bar-feedback]");
    expect(link.text()).toBe("Feedback");
    expect(link.attributes("target")).toBe("_blank");
    expect(link.attributes("rel")).toBe("noopener");
    const body = new URL(link.attributes("href")!).searchParams.get("body")!;
    expect(body).toContain("- page: `/examples/repressilator?q=laci`");
    expect(body).toContain("- model: the example `repressilator`");
  });

  it("names no report on a page which shows none, whatever the store still holds", async () => {
    const store = useReportStore();
    store.source = { kind: "example", id: "repressilator", name: "repressilator" };
    await router.push("/examples");
    const href = mountBar().get("[data-testid=app-bar-feedback]").attributes("href")!;
    const body = new URL(href).searchParams.get("body")!;
    expect(body).toContain("- page: `/examples`");
    expect(body).not.toContain("- model:");
  });
});
