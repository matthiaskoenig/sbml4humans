import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import type { Reaction, Species, Submodel, Uncertainty } from "@/api/types";
import { primevueOptions } from "@/assets/primevue";
import AttributesColumn from "@/components/inspector/AttributesColumn.vue";
import InspectorPanel from "@/components/inspector/InspectorPanel.vue";
import LinksColumn from "@/components/inspector/LinksColumn.vue";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import SubmodelAttributes from "@/components/inspector/attributes/SubmodelAttributes.vue";
import UncertaintyAttributes from "@/components/inspector/attributes/UncertaintyAttributes.vue";
import { ELEMENT_TYPES, DOCUMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { ReportIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const fixtures = [
  "repressilator",
  "icg_body",
  "fbc_example",
  "distrib_uncertainties",
  "model_definitions",
] as const;
const indexes = fixtures.map((name) => new ReportIndex(loadReport(name)));
const repressilator = indexes[0]!;

function mountWith(component: unknown, props: Record<string, unknown>, index: ReportIndex) {
  return mount(
    component as never,
    {
      props,
      global: {
        plugins: [router, [PrimeVue, primevueOptions]],
        directives: { tooltip: Tooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    } as never,
  );
}

describe("inspector", () => {
  it("has an attributes component for every type", () => {
    for (const info of [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES]) {
      expect(ATTRIBUTE_COMPONENTS[info.type], info.type).toBeDefined();
    }
  });

  it("renders the attributes of every element of the fixtures without error", async () => {
    await router.push("/examples/x");
    let rendered = 0;
    for (const index of indexes) {
      for (const element of index.elements.values()) {
        const wrapper = mountWith(AttributesColumn, { element }, index);
        expect(wrapper.find("[data-testid=attributes-column]").exists()).toBe(true);
        wrapper.unmount();
        rendered += 1;
      }
    }
    expect(rendered).toBeGreaterThan(300);
  });

  it("shows the species attributes with a compartment link", async () => {
    await router.push("/examples/BIOMD0000000012");
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(AttributesColumn, { element: species }, repressilator);
    expect(wrapper.text()).toContain("compartment");
    const link = wrapper.find("[data-testid=element-link]");
    expect(link.text()).toBe(species.compartment);
  });

  it("lists the reactants of a reaction with links to the species reference and the species", async () => {
    const reaction = repressilator.mainModel!.listOfReactions!.find(
      (r) => r.listOfReactants!.length > 0,
    ) as Reaction;
    const wrapper = mountWith(AttributesColumn, { element: reaction }, repressilator);
    const pks = wrapper.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain(reaction.listOfReactants![0]!.pk);
    expect(pks).toContain(
      repressilator.resolve(reaction.pk, "reactant", reaction.listOfReactants![0]!.species),
    );
  });

  it("shows an unresolved submodel conversion factor as plain text, not a link", () => {
    // no comp fixture sets a conversionFactor (`grep timeConversionFactor` over the resources
    // finds no hits, per the backend follow-up), so every submodel exercises this negative case.
    const compModels = new ReportIndex(loadReport("comp_models", "./models/omex_comp.xml"));
    const submodel = compModels.mainModel!.listOfSubmodels!.find(
      (sm) => sm.timeConversionFactor === null,
    ) as Submodel;
    const wrapper = mountWith(SubmodelAttributes, { element: submodel }, compModels);
    const row = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "time conversion factor")!;
    expect(row.find("a").exists()).toBe(false);
    expect(row.find("dd").text()).toBe("-");
  });

  it("groups the links by kind in both directions", async () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(LinksColumn, { pk: species.pk }, repressilator);
    const references = wrapper.get("[data-testid=links-references]");
    expect(references.text()).toContain("compartment");
    const referencedBy = wrapper.get("[data-testid=links-referenced-by]");
    expect(referencedBy.findAll("[data-testid=element-link]").length).toBeGreaterThan(0);
  });

  it("shows none for an element without edges", () => {
    const wrapper = mountWith(LinksColumn, { pk: "nope" }, repressilator);
    expect(wrapper.text()).toContain("none");
  });

  it("never renders the uncertainty definition url as a link unless it is http(s)", () => {
    const distrib = indexes[fixtures.indexOf("distrib_uncertainties")]!;
    const uncertainty = [...distrib.elements.values()].find(
      (element) => element.sbmlType === "Uncertainty",
    ) as Uncertainty;
    const unsafe: Uncertainty = {
      ...uncertainty,
      uncertParameters: [
        {
          var: null,
          value: null,
          units: null,
          type: "distribution",
          definitionUrl: "javascript:alert(1)",
          math: null,
        },
      ],
    };
    const wrapper = mountWith(UncertaintyAttributes, { element: unsafe }, distrib);
    expect(wrapper.find("a").exists()).toBe(false);
    expect(wrapper.text()).toContain("javascript:alert(1)");
  });

  it("renders the header of the panel", async () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(InspectorPanel, { pk: species.pk }, repressilator);
    expect(wrapper.get("[data-testid=inspector-type]").text()).toBe("Species");
    expect(wrapper.get("[data-testid=inspector-id]").text()).toBe(species.id);
    expect(wrapper.find("[data-testid=inspector-close]").exists()).toBe(true);
  });
});
