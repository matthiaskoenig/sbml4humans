import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SearchBox from "@/components/report/SearchBox.vue";
import { router } from "@/router";

const DEBOUNCE = 150;
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

describe("SearchBox", () => {
  it("writes the search to the route after the debounce", async () => {
    await router.push("/examples/BIOMD0000000012");
    const wrapper = mount(SearchBox, { global: { plugins: [router] } });
    await wrapper.find("[data-testid=search-input]").setValue("laci");
    await wait(DEBOUNCE + 50);
    expect(router.currentRoute.value.query.q).toBe("laci");
    wrapper.unmount();
  });

  it("drops a pending search when the page is left", async () => {
    await router.push("/examples/BIOMD0000000012");
    const wrapper = mount(SearchBox, { global: { plugins: [router] } });
    await wrapper.find("[data-testid=search-input]").setValue("laci");
    wrapper.unmount();
    await router.push("/examples/CompModels");
    await wait(DEBOUNCE + 50);
    expect(router.currentRoute.value.path).toBe("/examples/CompModels");
    expect(router.currentRoute.value.query.q).toBeUndefined();
  });
});
