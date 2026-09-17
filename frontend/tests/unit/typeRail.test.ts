import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { ElementType } from "@/api/types";
import TypeRail, { type TypeCount } from "@/components/report/TypeRail.vue";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const counts = new Map<ElementType, TypeCount>();

function mountRail() {
  return mount(TypeRail, {
    props: { index, model: index.mainModel!, counts },
    global: { plugins: [router] },
  });
}

describe("TypeRail", () => {
  it("scopes the toggle to the document's declared (core only) types", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
    const wrapper = mountRail();

    await wrapper.find("[data-testid=rail-toggle-Reaction]").trigger("change");
    await flushPromises();
    const types = router.currentRoute.value.query.types;
    expect(typeof types).toBe("string");
    const list = (types as string).split(",");
    expect(list).not.toContain("Reaction");
    expect(list).not.toContain("Submodel");
    expect(list).not.toContain("GeneProduct");

    await wrapper.find("[data-testid=rail-toggle-Reaction]").trigger("change");
    await flushPromises();
    expect(router.currentRoute.value.query.types).toBeUndefined();
  });

  it("drops an undeclared type of the route instead of clearing the filter", async () => {
    await router.push({ path: "/examples/BIOMD0000000012", query: {} });
    const wrapper = mountRail();
    const declared = wrapper
      .findAll("[data-testid^=rail-type-]")
      .map((row) => row.attributes("data-testid")!.replace("rail-type-", ""));
    expect(declared).toContain("Reaction");
    expect(declared).not.toContain("Submodel");

    // a `types=` of an older url of a comp document, carried over to this core only model
    await router.push({
      path: "/examples/BIOMD0000000012",
      query: { types: [...declared, "Submodel"].join(",") },
    });
    await flushPromises();
    await wrapper.find("[data-testid=rail-toggle-Reaction]").trigger("change");
    await flushPromises();
    expect(router.currentRoute.value.query.types).toBe(
      declared.filter((type) => type !== "Reaction").join(","),
    );
    wrapper.unmount();
  });
});
