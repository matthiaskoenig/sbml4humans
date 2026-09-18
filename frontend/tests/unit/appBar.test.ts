import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AppBar from "@/components/layout/AppBar.vue";
import { DOCS_URL } from "@/report/glossary";
import { router } from "@/router";

describe("AppBar", () => {
  it("links to the documentation site next to the examples link", () => {
    const wrapper = mount(AppBar, { global: { plugins: [router] } });
    const link = wrapper.get("[data-testid=app-bar-docs]");
    expect(link.attributes("href")).toBe(DOCS_URL);
    expect(link.attributes("target")).toBe("_blank");
    expect(link.attributes("rel")).toBe("noopener");
    expect(link.text()).toBe("Documentation");
  });

  it("shows the logo in the link to the home page", () => {
    const wrapper = mount(AppBar, { global: { plugins: [router] } });
    const logo = wrapper.get("[data-testid=app-logo]");
    expect(logo.element.tagName).toBe("IMG");
    expect(logo.attributes("src")).toContain("logo");
    expect(logo.attributes("alt")).toBeTruthy();
    // the logo and the wordmark are the same link to the home page
    const home = wrapper.get("a[href='/']");
    expect(home.find("[data-testid=app-logo]").exists()).toBe(true);
    expect(home.text()).toBe("SBML4Humans");
  });
});
