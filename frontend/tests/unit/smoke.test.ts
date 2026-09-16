import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "@/App.vue";

describe("App", () => {
  it("renders the app name", () => {
    const wrapper = mount(App);
    expect(wrapper.text()).toContain("SBML4Humans");
  });
});
