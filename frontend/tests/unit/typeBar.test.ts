import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { ElementType } from "@/api/types";
import TypeBar, { type TypeCount } from "@/components/report/TypeBar.vue";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const model = index.mainModel!;

/** The counts of the model, the way the report page builds them: every element of a type counts
 * as a match unless `matched` names a smaller number for that type. */
function countsOf(matched: Partial<Record<ElementType, number>> = {}): Map<ElementType, TypeCount> {
  const counts = new Map<ElementType, TypeCount>();
  for (const [type, elements] of index.byType(model.id!)) {
    counts.set(type, { total: elements.length, matched: matched[type] ?? elements.length });
  }
  return counts;
}

function mountBar(counts = countsOf()) {
  return mount(TypeBar, {
    props: { index, model, counts },
    global: { plugins: [router] },
  });
}

function listedTypes(wrapper: ReturnType<typeof mountBar>): string[] {
  return wrapper
    .findAll("[data-testid^=bar-type-]")
    .map((entry) => entry.attributes("data-testid")!.replace("bar-type-", ""));
}

describe("TypeBar", () => {
  it("lists the types the model has elements of and leaves out the empty ones", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
    const wrapper = mountBar();
    const types = listedTypes(wrapper);
    // the repressilator states species, reactions and parameters, and no event and no constraint
    expect(types).toContain("Species");
    expect(types).toContain("Reaction");
    expect(types).toContain("Parameter");
    expect(types).not.toContain("Event");
    expect(types).not.toContain("Constraint");
    // a type of a package the document does not declare is not listed either
    expect(types).not.toContain("Submodel");
    expect(wrapper.get("[data-testid=bar-count-Species]").text()).toBe("6");
    wrapper.unmount();
  });

  it("shows the document and the model of the report", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
    const wrapper = mountBar();
    expect(wrapper.get("[data-testid=bar-document]").text()).toContain("SBMLDocument");
    expect(wrapper.get("[data-testid=bar-model]").text()).toContain("BIOMD0000000012");
    wrapper.unmount();
  });

  it("counts the matches in front of the total while a search is active", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: { q: "laci" } });
    const wrapper = mountBar(countsOf({ Species: 2, Reaction: 0 }));
    expect(wrapper.get("[data-testid=bar-count-Species]").text()).toBe("2 / 6");
    // a type whose elements the search filtered away keeps its entry and says so
    expect(listedTypes(wrapper)).toContain("Reaction");
    expect(wrapper.get("[data-testid=bar-count-Reaction]").text()).toBe("0 / 12");
    wrapper.unmount();
  });

  it("scopes the toggle to the document's declared (core only) types", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
    const wrapper = mountBar();

    await wrapper.find("[data-testid=bar-toggle-Reaction]").trigger("change");
    await flushPromises();
    const types = router.currentRoute.value.query.types;
    expect(typeof types).toBe("string");
    const list = (types as string).split(",");
    expect(list).not.toContain("Reaction");
    expect(list).not.toContain("Submodel");
    expect(list).not.toContain("GeneProduct");

    await wrapper.find("[data-testid=bar-toggle-Reaction]").trigger("change");
    await flushPromises();
    expect(router.currentRoute.value.query.types).toBeUndefined();
    wrapper.unmount();
  });

  it("drops an undeclared type of the route instead of clearing the filter", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
    const wrapper = mountBar();
    const declared = listedTypes(wrapper);
    expect(declared).toContain("Reaction");
    expect(declared).not.toContain("Submodel");

    // a `types=` of an older url of a comp document, carried over to this core only model
    await router.push({
      path: "/examples/BIOMD0000000012",
      query: { types: [...declared, "Submodel"].join(",") },
    });
    await flushPromises();
    await wrapper.find("[data-testid=bar-toggle-Reaction]").trigger("change");
    await flushPromises();
    expect(router.currentRoute.value.query.types).toBe(
      declared.filter((type) => type !== "Reaction").join(","),
    );
    wrapper.unmount();
  });
});
