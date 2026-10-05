import { createPinia } from "pinia";
import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import App from "@/App.vue";
import { router } from "@/router";

// the home page is rendered through the router, the real one with its lazy pages
vi.unmock("@/router");

describe("App", () => {
  it("renders the home page", async () => {
    await router.push("/");
    await router.isReady();
    const wrapper = mount(App, { global: { plugins: [createPinia(), router] } });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(wrapper.text()).toContain("SBML4Humans");
  });
});
