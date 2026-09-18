import * as floating from "@floating-ui/dom";
import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, withDirectives } from "vue";

import { TOOLTIP_ID, vTooltip } from "@/directives/tooltip";

vi.mock("@floating-ui/dom", async (importOriginal) => {
  const original = await importOriginal<typeof floating>();
  return { ...original, computePosition: vi.fn(async () => ({ x: 12.4, y: 30.6 })) };
});

const computePosition = vi.mocked(floating.computePosition);

/** A span with the tooltip below it, as the call sites use it. */
const Host = defineComponent({
  props: {
    text: { type: String, required: false, default: undefined },
    mono: { type: Boolean, default: false },
  },
  setup(props) {
    return () =>
      withDirectives(h("span", { "data-testid": "host", tabindex: 0 }, "value"), [
        [vTooltip, props.text, "", { bottom: true, mono: props.mono }],
      ]);
  },
});

let wrapper: { unmount(): void } | null = null;

function mountHost(text: string | undefined, mono = false) {
  const mounted = mount(Host, { props: { text, mono }, attachTo: document.body });
  wrapper = mounted;
  return mounted;
}

const tooltip = () => document.getElementById(TOOLTIP_ID);
const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
  computePosition.mockClear();
});

describe("v-tooltip", () => {
  it("shows the text on mouseenter and hides it on mouseleave", async () => {
    const host = mountHost("kd_mRNA * X (click to copy)").get("[data-testid=host]");
    await host.trigger("mouseenter");
    expect(tooltip()?.hidden).toBe(false);
    expect(tooltip()?.textContent).toBe("kd_mRNA * X (click to copy)");
    expect(tooltip()?.getAttribute("role")).toBe("tooltip");
    expect(host.attributes("aria-describedby")).toBe(TOOLTIP_ID);
    await host.trigger("mouseleave");
    expect(tooltip()?.hidden).toBe(true);
    expect(host.attributes("aria-describedby")).toBeUndefined();
  });

  it("positions the tooltip with the placement of the modifier", async () => {
    await mountHost("0.123456789").get("[data-testid=host]").trigger("mouseenter");
    await flush();
    expect(computePosition).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      tooltip(),
      expect.objectContaining({ placement: "bottom", strategy: "fixed" }),
    );
    expect(tooltip()?.style.transform).toBe("translate(12px, 31px)");
  });

  it("shows an explanation in the font of the text and a value in monospace", async () => {
    // the explanations of the glossary are sentences, the ids, values and formulas are not
    await mountHost("the identifier of the element")
      .get("[data-testid=host]")
      .trigger("mouseenter");
    expect(tooltip()?.className).not.toContain("font-mono");
    wrapper?.unmount();
    await mountHost("kd_mRNA * X", true).get("[data-testid=host]").trigger("mouseenter");
    expect(tooltip()?.className).toContain("font-mono");
  });

  it("shows on keyboard focus and hides on Escape", async () => {
    await mountHost("value").get("[data-testid=host]").trigger("focusin");
    expect(tooltip()?.hidden).toBe(false);
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(tooltip()?.hidden).toBe(true);
  });

  it("shows nothing without a text", async () => {
    const host = mountHost(undefined).get("[data-testid=host]");
    await host.trigger("mouseenter");
    expect(tooltip()?.hidden ?? true).toBe(true);
    expect(host.attributes("aria-describedby")).toBeUndefined();
  });

  it("updates the text while shown and hides when the text goes away", async () => {
    const host = mountHost("first");
    await host.get("[data-testid=host]").trigger("mouseenter");
    await host.setProps({ text: "second" });
    expect(tooltip()?.textContent).toBe("second");
    await host.setProps({ text: undefined });
    expect(tooltip()?.hidden).toBe(true);
  });

  it("hides on a scroll and when the element is unmounted", async () => {
    const host = mountHost("value");
    await host.get("[data-testid=host]").trigger("mouseenter");
    document.dispatchEvent(new Event("scroll"));
    expect(tooltip()?.hidden).toBe(true);
    await host.get("[data-testid=host]").trigger("mouseenter");
    expect(tooltip()?.hidden).toBe(false);
    host.unmount();
    wrapper = null;
    expect(tooltip()?.hidden).toBe(true);
  });
});
