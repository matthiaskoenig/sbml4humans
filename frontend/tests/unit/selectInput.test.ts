import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SelectInput from "@/components/input/SelectInput.vue";

const options = [
  { label: "./models/omex_minimal.xml", value: "./models/omex_minimal.xml" },
  { label: "m1 (definition)", value: "m1" },
];

describe("SelectInput", () => {
  it("renders the options with the selected value and the attributes on the select", () => {
    const wrapper = mount(SelectInput, {
      props: { modelValue: "m1", options },
      attrs: { "aria-label": "model", "data-testid": "model-select" },
    });
    const select = wrapper.get("select");
    expect(select.attributes("aria-label")).toBe("model");
    expect(select.attributes("data-testid")).toBe("model-select");
    expect(wrapper.attributes("aria-label")).toBeUndefined();
    expect(wrapper.findAll("option").map((option) => option.text())).toEqual([
      "./models/omex_minimal.xml",
      "m1 (definition)",
    ]);
    expect((select.element as HTMLSelectElement).value).toBe("m1");
    expect(wrapper.get("svg").classes()).toContain("lucide-chevron-down");
  });

  it("emits the chosen value", async () => {
    const wrapper = mount(SelectInput, {
      props: { modelValue: "./models/omex_minimal.xml", options },
    });
    await wrapper.get("select").setValue("m1");
    expect(wrapper.emitted("update:modelValue")).toEqual([["m1"]]);
  });

  it("follows a new model value", async () => {
    const wrapper = mount(SelectInput, {
      props: { modelValue: "./models/omex_minimal.xml", options },
    });
    await wrapper.setProps({ modelValue: "m1" });
    expect((wrapper.get("select").element as HTMLSelectElement).value).toBe("m1");
  });
});
