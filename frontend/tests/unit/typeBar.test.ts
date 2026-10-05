import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import type { ElementType, Model } from "@/api/types";
import TypeBar, { type TypeCount } from "@/components/report/TypeBar.vue";
import { ValidationIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { ValidationIndex } from "@/report/validationIndex";
import { router } from "@/router";

import { loadReport, loadValidation, withIssues } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const model = index.mainModel!;

/** The mount options of the bar with the validation of its report, null while it is pending. */
function globalWith(validation: ValidationIndex | null = null) {
  return { plugins: [router], provide: { [ValidationIndexKey as symbol]: ref(validation) } };
}

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
    global: globalWith(),
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

  it("marks a type with an issue by the worst severity of its elements", async () => {
    const validation = new ReportIndex(loadReport("validation"));
    const counts = new Map<ElementType, TypeCount>();
    for (const [type, elements] of validation.byType(validation.mainModel!.id!)) {
      counts.set(type, { total: elements.length, matched: elements.length });
    }
    await router.push({ path: "/report", query: {} });
    const wrapper = mount(TypeBar, {
      props: { index: validation, model: validation.mainModel!, counts },
      global: globalWith(new ValidationIndex(validation, loadValidation("validation"))),
    });
    const parameter = wrapper.get("[data-testid=bar-type-Parameter]");
    expect(parameter.find("[data-testid=severity-warning]").exists()).toBe(true);
    expect(parameter.find("[data-testid=bar-issue-Parameter]").exists()).toBe(true);
    // the species of the fixture have no issue, so their entry carries no mark
    const species = wrapper.get("[data-testid=bar-type-Species]");
    expect(species.find("[data-testid^=severity-]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("marks a type for the issues of the model of the bar alone", async () => {
    // both models of the fixture state a species, the warnings concern the species of m1 alone
    const definitions = new ReportIndex(loadReport("model_definitions"));
    await router.push({ path: "/report", query: {} });
    const markOf = (model: Model) => {
      const counts = new Map<ElementType, TypeCount>();
      for (const [type, elements] of definitions.byType(model.id!)) {
        counts.set(type, { total: elements.length, matched: elements.length });
      }
      const wrapper = mount(TypeBar, {
        props: { index: definitions, model, counts },
        global: globalWith(
          new ValidationIndex(
            definitions,
            withIssues([{ pk: "m1/Species:A", severity: "warning" }]),
          ),
        ),
      });
      const marked = wrapper.find("[data-testid=bar-issue-Species]").exists();
      wrapper.unmount();
      return marked;
    };
    expect(markOf(definitions.mainModel!)).toBe(false);
    expect(markOf(definitions.model("m1")!)).toBe(true);
  });

  /** The bar of the main model of an index, every element of a type counted as a match. */
  function mountBarOf(of: ReportIndex, validation: ValidationIndex | null) {
    const counts = new Map<ElementType, TypeCount>();
    for (const [type, elements] of of.byType(of.mainModel!.id!)) {
      counts.set(type, { total: elements.length, matched: elements.length });
    }
    return mount(TypeBar, {
      props: { index: of, model: of.mainModel!, counts },
      global: globalWith(validation),
    });
  }

  it("marks the model, which has no row of its own, by its worst severity", async () => {
    // the one error of the validation example, 10601, is an issue of the model
    const validation = new ReportIndex(loadReport("validation"));
    await router.push({ path: "/report", query: {} });
    const wrapper = mountBarOf(
      validation,
      new ValidationIndex(validation, loadValidation("validation")),
    );
    const model = wrapper.get("[data-testid=bar-model]");
    expect(model.find("[data-testid=bar-issue-model]").exists()).toBe(true);
    expect(model.find("[data-testid=severity-error]").exists()).toBe(true);
    expect(
      wrapper.get("[data-testid=bar-document]").find("[data-testid^=severity-]").exists(),
    ).toBe(false);
    wrapper.unmount();
  });

  it("marks the document and an external model definition by their issues, a note alone not", async () => {
    const comp = new ReportIndex(loadReport("comp_models", "./models/omex_comp.xml"));
    const marked = new ValidationIndex(
      comp,
      withIssues([
        { pk: comp.document.pk, severity: "warning" },
        { pk: "document/ExternalModelDefinition:emd1", severity: "error", rule: 1090101 },
        { pk: "document/ExternalModelDefinition:emd2", severity: "info" },
      ]),
    );
    await router.push({ path: "/report", query: {} });
    const wrapper = mountBarOf(comp, marked);
    const document = wrapper.get("[data-testid=bar-document]");
    expect(document.find("[data-testid=bar-issue-document]").exists()).toBe(true);
    expect(document.find("[data-testid=severity-warning]").exists()).toBe(true);
    const emds = wrapper.findAll("[data-testid=bar-emd]");
    const emd = (id: string) => emds.find((button) => button.text().includes(id))!;
    expect(emd("emd1").find("[data-testid=severity-error]").exists()).toBe(true);
    expect(emd("emd1").find("[data-testid=bar-issue-emd]").exists()).toBe(true);
    expect(emd("emd2").find("[data-testid^=severity-]").exists()).toBe(false);
    expect(emd("emd0").find("[data-testid^=severity-]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("marks the model by the issue of a list of the model, which has no row", async () => {
    const report = new ReportIndex(loadReport("list_of"));
    const marked = new ValidationIndex(
      report,
      withIssues([{ pk: "list_of/ListOf:metabolites", severity: "warning" }]),
    );
    await router.push({ path: "/report", query: {} });
    const wrapper = mountBarOf(report, marked);
    expect(
      wrapper.get("[data-testid=bar-model]").find("[data-testid=severity-warning]").exists(),
    ).toBe(true);
    wrapper.unmount();
  });

  it("marks nothing while the validation is pending", async () => {
    const validation = new ReportIndex(loadReport("validation"));
    await router.push({ path: "/report", query: {} });
    const wrapper = mountBarOf(validation, null);
    expect(wrapper.find("[data-testid^=severity-]").exists()).toBe(false);
    wrapper.unmount();
  });
});
