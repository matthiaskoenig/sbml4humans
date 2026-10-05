import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SearchBox from "@/components/report/SearchBox.vue";
import { router } from "@/router";

const DEBOUNCE = 150;

describe("SearchBox", () => {
  // the debounce runs on fake timers, so that a loaded machine does not decide when it ends
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("writes the search to the route after the debounce", async () => {
    await router.push("/examples/BIOMD0000000012");
    const wrapper = mount(SearchBox, { global: { plugins: [router] } });
    await wrapper.find("[data-testid=search-input]").setValue("laci");
    await vi.advanceTimersByTimeAsync(DEBOUNCE - 1);
    expect(router.currentRoute.value.query.q).toBeUndefined();
    await vi.advanceTimersByTimeAsync(1);
    await vi.waitFor(() => expect(router.currentRoute.value.query.q).toBe("laci"));
    wrapper.unmount();
  });

  it("drops a pending search when the page is left", async () => {
    await router.push("/examples/BIOMD0000000012");
    const wrapper = mount(SearchBox, { global: { plugins: [router] } });
    await wrapper.find("[data-testid=search-input]").setValue("laci");
    wrapper.unmount();
    await router.push("/examples/CompModels");
    await vi.advanceTimersByTimeAsync(DEBOUNCE * 2);
    expect(router.currentRoute.value.path).toBe("/examples/CompModels");
    expect(router.currentRoute.value.query.q).toBeUndefined();
  });
});
