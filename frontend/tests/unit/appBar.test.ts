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
});
