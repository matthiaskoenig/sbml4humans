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

  it("renders a line per line of the xml, highlighted and hanging below its indentation", () => {
    const xml = '<rdf:li rdf:resource="https://x.org/a"/>\n\n  <b>K</b>';
    const wrapper = mount(XmlView, { props: { xml } });
    const lines = wrapper.findAll("[data-testid=xml-line]");
    expect(lines.map((line) => line.element.textContent)).toEqual([
      '<rdf:li rdf:resource="https://x.org/a"/>',
      "",
      "  <b>K</b>",
    ]);
    expect(lines[2]!.attributes("style")).toContain("padding-left: 6ch");
    expect(lines[2]!.attributes("style")).toContain("text-indent: -6ch");
    expect(lines[0]!.findAll("wbr")).toHaveLength(2);
    expect(lines[0]!.get("span.text-blue-700").text()).toBe("li");
    expect(lines[0]!.get("span.text-emerald-700").text()).toBe('"https://x.org/a"');
    expect(lines[1]!.find("br").exists()).toBe(true);
    expect(lines[2]!.findAll("span.font-semibold").map((span) => span.text())).toEqual(["", "K"]);
  });

  it("renders the empty message and no copy button when xml is absent", () => {
    const wrapper = mount(XmlView, { props: { xml: null } });
    expect(wrapper.text()).toContain("No XML available.");
    expect(wrapper.find("pre").exists()).toBe(false);
    expect(wrapper.find("[data-testid=xml-copy]").exists()).toBe(false);
  });

  it("clears the pending state reset when it is unmounted", async () => {
    vi.useFakeTimers();
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      configurable: true,
    });
    const wrapper = mount(XmlView, { props: { xml: "<model/>" } });
    await wrapper.get("[data-testid=xml-copy]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-testid=xml-copy]").text()).toBe("Copied");
    expect(vi.getTimerCount()).toBe(1);
    wrapper.unmount();
    expect(vi.getTimerCount()).toBe(0);
    vi.useRealTimers();
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
