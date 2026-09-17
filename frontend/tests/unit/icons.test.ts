import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import LoadingState from "@/components/layout/LoadingState.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import { DOCUMENT_TYPES, ELEMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { vTooltip } from "@/directives/tooltip";
import { typeEntry } from "@/report/glossary";

describe("icons", () => {
  it("renders the svg icon of every type in both sizes", () => {
    for (const info of [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES]) {
      const small = mount(TypeMark, { props: { type: info.type } });
      const svg = small.get("svg");
      expect(svg.classes(), info.type).toContain("size-2.5");
      expect(svg.attributes("aria-hidden")).toBe("true");
      expect(
        mount(TypeMark, { props: { type: info.type, size: "md" } })
          .get("svg")
          .classes(),
      ).toContain("size-3.5");
    }
    expect(
      mount(TypeMark, { props: { type: "Reaction" } })
        .get("svg")
        .classes(),
    ).toContain("lucide-arrow-right-left");
  });

  it("shows the summary of the type as a tooltip", async () => {
    const wrapper = mount(TypeMark, {
      props: { type: "Species" },
      attachTo: document.body,
      global: { directives: { tooltip: vTooltip } },
    });
    await wrapper.trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(typeEntry("Species")?.summary);
    wrapper.unmount();
  });

  it("labels the check mark of a true value", () => {
    const check = mount(BooleanMark, { props: { value: true } }).get("svg");
    // inline, the check sits on the text instead of the top of the line
    expect(check.classes()).toEqual(expect.arrayContaining(["inline-block", "size-3.25"]));
    expect(check.attributes("aria-label")).toBe("true");
    expect(check.attributes("role")).toBe("img");
    expect(check.attributes("aria-hidden")).toBeUndefined();
    expect(
      mount(BooleanMark, { props: { value: false } })
        .find("svg")
        .exists(),
    ).toBe(false);
  });

  it("spins the loading icon", () => {
    const wrapper = mount(LoadingState, { props: { message: "Loading" } });
    expect(wrapper.get("svg").classes()).toContain("animate-spin");
  });
});
