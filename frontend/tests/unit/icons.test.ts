import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import LoadingState from "@/components/layout/LoadingState.vue";
import BooleanMark from "@/components/misc/BooleanMark.vue";
import TypeMark from "@/components/misc/TypeMark.vue";
import { DOCUMENT_TYPES, ELEMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";

describe("icons", () => {
  it("renders the svg icon of every type in both sizes", () => {
    for (const info of [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES]) {
      const small = mount(TypeMark, { props: { type: info.type } });
      const svg = small.get("svg");
      expect(svg.classes(), info.type).toContain("size-2.5");
      expect(svg.attributes("aria-hidden")).toBe("true");
      expect(small.attributes("title")).toBe(info.label);
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
