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

/** Whether the element answers `:focus-visible`, which the directive asks a focus it receives.
 * jsdom implements the selector and answers `false` to it, whatever has the focus, so a test of
 * the keyboard has to say so itself. */
function focusVisible(element: Element, visible: boolean): void {
  const matches = element.matches.bind(element);
  vi.spyOn(element, "matches").mockImplementation((selector: string) =>
    selector === ":focus-visible" ? visible : matches(selector),
  );
}

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
  computePosition.mockClear();
});

describe("v-tooltip", () => {
  it("shows nothing for the mouseenter a touch is followed by", async () => {
    const host = mountHost("the identifier of the element").get("[data-testid=host]");
    // a finger does not hover: the browser sends the mouse events of a tap after its touch, and
    // no mouseleave follows them until the next tap somewhere else
    const touch = new Event("pointerdown", { bubbles: true });
    Object.defineProperty(touch, "pointerType", { value: "touch" });
    host.element.dispatchEvent(touch);
    await host.trigger("mouseenter");
    expect(tooltip()?.hidden ?? true).toBe(true);

    // the mouse of the same device hovers again
    const mouse = new Event("pointermove", { bubbles: true });
    Object.defineProperty(mouse, "pointerType", { value: "mouse" });
    host.element.dispatchEvent(mouse);
    await host.trigger("mouseenter");
    expect(tooltip()?.hidden).toBe(false);
  });

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
    const host = mountHost("value").get("[data-testid=host]");
    focusVisible(host.element, true);
    await host.trigger("focusin");
    expect(tooltip()?.hidden).toBe(false);
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(tooltip()?.hidden).toBe(true);
  });

  // the browser restores the focus to the label which opened the help dialog when it closes: a
  // tooltip on that label would stand next to a pointer which is somewhere else entirely
  it("shows nothing on a focus the pointer or a script caused", async () => {
    const host = mountHost("value").get("[data-testid=host]");
    focusVisible(host.element, false);
    await host.trigger("focusin");
    expect(tooltip()?.hidden ?? true).toBe(true);
    expect(host.attributes("aria-describedby")).toBeUndefined();
    // the pointer shows it as it always did
    await host.trigger("mouseenter");
    expect(tooltip()?.hidden).toBe(false);
  });

  it("shows on focus where the engine does not know the selector", async () => {
    const host = mountHost("value").get("[data-testid=host]");
    vi.spyOn(host.element, "matches").mockImplementation(() => {
      throw new Error("unknown pseudo-class :focus-visible");
    });
    await host.trigger("focusin");
    expect(tooltip()?.hidden).toBe(false);
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

  // a modal dialog, the help dialog of the report, is painted in the top layer, above everything
  // the page itself paints: a tooltip which stayed in the body would be covered by its backdrop
  it("puts the tooltip into an open dialog and back into the body after it", async () => {
    const dialog = document.createElement("dialog");
    dialog.setAttribute("open", "");
    document.body.appendChild(dialog);
    const inside = mount(Host, { props: { text: "in the dialog" }, attachTo: dialog });
    await inside.get("[data-testid=host]").trigger("mouseenter");
    expect(tooltip()?.parentElement).toBe(dialog);
    expect(tooltip()?.textContent).toBe("in the dialog");
    inside.unmount();
    dialog.remove();

    const host = mountHost("on the page").get("[data-testid=host]");
    await host.trigger("mouseenter");
    expect(tooltip()?.parentElement).toBe(document.body);
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
