import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h } from "vue";

import { useReportView } from "@/report/view";
import { router } from "@/router";

let view: ReturnType<typeof useReportView>;

const Probe = defineComponent({
  setup() {
    view = useReportView();
    return () => h("div");
  },
});

describe("useReportView", () => {
  beforeEach(async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("replaces the route for the search and pushes the selection and the types", async () => {
    const wrapper = mount(Probe, { global: { plugins: [router] } });
    const push = vi.spyOn(router, "push");
    const replace = vi.spyOn(router, "replace");

    await view.setSearch("laci");
    expect(replace).toHaveBeenCalledTimes(1);
    expect(push).not.toHaveBeenCalled();
    expect(router.currentRoute.value.query.q).toBe("laci");

    const pk = "BIOMD0000000012/Species:PX";
    await view.select(pk);
    expect(push).toHaveBeenCalledTimes(1);
    expect(router.currentRoute.value.query.pk).toBe(pk);

    await view.setTypes(["Species"]);
    expect(push).toHaveBeenCalledTimes(2);
    expect(replace).toHaveBeenCalledTimes(1);
    expect(router.currentRoute.value.query.types).toBe("Species");
    // the other view state survives an update
    expect(router.currentRoute.value.query.q).toBe("laci");
    expect(router.currentRoute.value.query.pk).toBe(pk);

    await view.select(null, "replace");
    expect(replace).toHaveBeenCalledTimes(2);
    expect(push).toHaveBeenCalledTimes(2);
    expect(router.currentRoute.value.query.pk).toBeUndefined();
    wrapper.unmount();
  });

  it("keeps the url of a loaded report out of the view state", async () => {
    await router.push({ path: "/report", query: { url: "https://example.org/model.xml" } });
    const wrapper = mount(Probe, { global: { plugins: [router] } });
    await view.setSearch("laci");
    expect(router.currentRoute.value.query.url).toBe("https://example.org/model.xml");
    expect(router.currentRoute.value.query.q).toBe("laci");
    wrapper.unmount();
  });
});
