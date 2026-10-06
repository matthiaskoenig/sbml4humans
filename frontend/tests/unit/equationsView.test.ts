import { flushPromises, mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import EquationBlock from "@/components/equations/EquationBlock.vue";
import EquationsView from "@/components/equations/EquationsView.vue";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const report = loadReport("repressilator");
const repressilator = new ReportIndex(report);

function mountView(index: ReportIndex) {
  return mount(EquationsView, {
    props: { index, location: "./model.xml" },
    global: {
      plugins: [router, createPinia()],
      provide: { [ReportIndexKey as symbol]: ref(index) },
    },
  });
}

describe("EquationsView", () => {
  it("shows the sections of the system with their counts", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: { view: "equations" } });
    const wrapper = mountView(repressilator);
    const count = (concept: string) =>
      wrapper.get(`[data-testid=equations-${concept}] [data-testid=equations-count]`).text();
    expect(count("odeSystem")).toBe("6");
    expect(count("reactionRates")).toBe("12");
    expect(count("odeAssignments")).toBe("9");
    // the repressilator has no event, no function definition and no initial value of a formula
    expect(wrapper.find("[data-testid=equations-odeEvents]").exists()).toBe(false);
    expect(wrapper.findAll("[data-testid=equation-row]")).toHaveLength(27);
    expect(wrapper.find("[data-testid=equations-unsupported]").exists()).toBe(false);
    expect(wrapper.find("[data-testid=equations-tabs]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("orders the sections from the definitions to the system", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: { view: "equations" } });
    const index = new ReportIndex({
      ...report,
      odeSystem: {
        ...report.odeSystem!,
        functions: [{ variable: null, lhs: "f(x)", lines: ["x"], origin: "function" }],
        initial: [{ variable: null, lhs: "y", lines: ["1 + 2"], origin: "initial_assignment" }],
      },
    });
    const wrapper = mountView(index);
    const order = wrapper
      .findAll("section[data-testid^=equations-]")
      .map((section) => section.attributes("data-testid"));
    expect(order).toEqual([
      "equations-odeFunctions",
      "equations-odeAssignments",
      "equations-reactionRates",
      "equations-odeSystem",
      "equations-odeInitial",
    ]);
    wrapper.unmount();
  });

  it("shows the code of a format in place of the math", async () => {
    await router.push({
      path: "/examples/BIOMD0000000012",
      query: { view: "equations", code: "julia" },
    });
    const wrapper = mountView(repressilator);
    expect(wrapper.find("[data-testid=equations-code]").exists()).toBe(true);
    expect(wrapper.find("[data-testid=equation-row]").exists()).toBe(false);
    expect(wrapper.get("[data-testid=equations-tab-julia]").attributes("aria-selected")).toBe(
      "true",
    );
    await wrapper.get("[data-testid=equations-tab-math]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.code).toBeUndefined();
    expect(wrapper.find("[data-testid=equation-row]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("selects the element of a symbol which is clicked", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: { view: "equations" } });
    const wrapper = mountView(repressilator);
    const symbol = wrapper.get('[data-pk="BIOMD0000000012/Reaction:Reaction4"]');
    await symbol.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe("BIOMD0000000012/Reaction:Reaction4");
    expect(router.currentRoute.value.query.view).toBe("equations");
    // the row of the equation of the selected element is marked
    const row = wrapper.get('[data-equation-of="BIOMD0000000012/Reaction:Reaction4"]');
    expect(row.classes()).toContain("bg-selected");
    wrapper.unmount();
  });

  it("names the constructs the system leaves out", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: { view: "equations" } });
    const index = new ReportIndex({
      ...report,
      odeSystem: {
        ...report.odeSystem!,
        unsupported: [{ kind: "algebraic rule", element: null }],
      },
    });
    const wrapper = mountView(index);
    expect(wrapper.get("[data-testid=equations-unsupported]").text()).toContain("algebraic rule");
    wrapper.unmount();
  });

  it("shows the failure to build the system in place of the equations", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: { view: "equations" } });
    const index = new ReportIndex({ ...report, odeSystem: null, odeError: "could not flatten" });
    const wrapper = mountView(index);
    expect(wrapper.get("[data-testid=error-message]").text()).toBe("could not flatten");
    expect(wrapper.find("[data-testid=equation-row]").exists()).toBe(false);
    expect(wrapper.find("[data-testid=equations-tabs]").exists()).toBe(false);
    wrapper.unmount();
  });
});

describe("EquationBlock", () => {
  it("shows the equation of an element and opens it in the view", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
    const wrapper = mount(EquationBlock, {
      props: { pk: "BIOMD0000000012/Species:PX" },
      global: { plugins: [router], provide: { [ReportIndexKey as symbol]: ref(repressilator) } },
    });
    expect(wrapper.findAll("[data-testid=equation-row]")).toHaveLength(1);
    expect(wrapper.text()).toContain("ODE system");
    await wrapper.get("[data-testid=equation-block-show]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.view).toBe("equations");
    wrapper.unmount();
  });

  it("shows nothing for an element without an equation", async () => {
    const wrapper = mount(EquationBlock, {
      props: { pk: "BIOMD0000000012/Compartment:cell" },
      global: { plugins: [router], provide: { [ReportIndexKey as symbol]: ref(repressilator) } },
    });
    expect(wrapper.find("[data-testid=equation-block]").exists()).toBe(false);
    wrapper.unmount();
  });
});
