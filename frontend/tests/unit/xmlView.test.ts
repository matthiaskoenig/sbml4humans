import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import XmlView from "@/components/misc/XmlView.vue";

describe("XmlView", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the xml and an active copy button when xml is present", () => {
    const wrapper = mount(XmlView, { props: { xml: "<model/>" } });
    expect(wrapper.get("pre").text()).toContain("<model/>");
    expect(wrapper.get("[data-testid=xml-copy]").text()).toBe("Copy");
  });

  it("renders the empty message and no copy button when xml is absent", () => {
    const wrapper = mount(XmlView, { props: { xml: null } });
    expect(wrapper.text()).toContain("No XML available.");
    expect(wrapper.find("pre").exists()).toBe(false);
    expect(wrapper.find("[data-testid=xml-copy]").exists()).toBe(false);
  });

  it("shows a failed state when the clipboard write rejects", async () => {
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: vi.fn().mockRejectedValue(new Error("denied")) },
      configurable: true,
    });
    const wrapper = mount(XmlView, { props: { xml: "<model/>" } });
    await wrapper.get("[data-testid=xml-copy]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-testid=xml-copy]").text()).toBe("Failed");
  });
});
