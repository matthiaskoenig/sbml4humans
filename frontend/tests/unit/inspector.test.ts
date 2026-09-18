import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import type {
  Constraint,
  Event,
  Reaction,
  Species,
  Submodel,
  Uncertainty,
  UnitDefinition,
} from "@/api/types";
import AttributesColumn from "@/components/inspector/AttributesColumn.vue";
import InspectorPanel from "@/components/inspector/InspectorPanel.vue";
import LinksColumn from "@/components/inspector/LinksColumn.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import GeneAssociationView from "@/components/misc/GeneAssociationView.vue";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import ReactionAttributes from "@/components/inspector/attributes/ReactionAttributes.vue";
import ReplacedElementAttributes from "@/components/inspector/attributes/ReplacedElementAttributes.vue";
import SubmodelAttributes from "@/components/inspector/attributes/SubmodelAttributes.vue";
import UncertaintyAttributes from "@/components/inspector/attributes/UncertaintyAttributes.vue";
import { ELEMENT_TYPES, DOCUMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { vTooltip } from "@/directives/tooltip";
import { ReportIndexKey } from "@/report/context";
import { attributeEntry, linkEntry, referenceUrl } from "@/report/glossary";
import { LIST_LIMIT } from "@/report/limitedList";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";
import { summaryOf } from "./summary";

const fixtures = [
  "repressilator",
  "icg_body",
  "fbc_example",
  "distrib_uncertainties",
  "model_definitions",
] as const;
const indexes = fixtures.map((name) => new ReportIndex(loadReport(name)));
const repressilator = indexes[0]!;
const constraintEvent = new ReportIndex(loadReport("constraint_event"));
const compDeletion = new ReportIndex(loadReport("comp_deletion"));
const fbcConstraints = new ReportIndex(loadReport("fbc_constraints_v3"));

/** A minimal index for the links list size tests: one "compartment" edge per target pk out of
 * the given source, nothing else, so the numbers stay exact and independent of the fixtures. */
function fakeLinksIndex(bySource: Record<string, string[]>): ReportIndex {
  return {
    references: (pk: string) =>
      (bySource[pk] ?? []).map((target) => ({ source: pk, target, kind: "compartment" as const })),
    referencedBy: () => [],
    get: (pk: string) => ({ pk, id: pk, metaId: null, sbmlType: undefined }),
  } as unknown as ReportIndex;
}

function mountWith(component: unknown, props: Record<string, unknown>, index: ReportIndex) {
  return mount(
    component as never,
    {
      props,
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
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

  // one mount per element of all fixtures, which takes more than the default 5 s on the
  // GitHub runner while the other test files run in parallel
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
  }, 30_000);

  it("shows the species attributes with a compartment link", async () => {
    await router.push("/examples/BIOMD0000000012");
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(AttributesColumn, { element: species }, repressilator);
    expect(wrapper.text()).toContain("compartment");
    const link = wrapper.find("[data-testid=element-link]");
    expect(link.text()).toBe(species.compartment);
  });

  it("shows the summary of the attribute as the tooltip of an attribute row's label", async () => {
    await router.push("/examples/BIOMD0000000012");
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(AttributesColumn, { element: species }, repressilator);
    const row = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "compartment")!;
    await row.get("dt").trigger("mouseenter");
    // the tooltip names the truncated label of the row before it explains it
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      `compartment: ${summaryOf(attributeEntry("Species", "compartment"), "Species.compartment")}`,
    );
  });

  it("shows the summary of the link kind as the tooltip of a link group's label", async () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mount(LinksColumn, {
      props: { pk: species.pk },
      attachTo: document.body,
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(repressilator) },
      },
    });
    const dt = wrapper
      .get("[data-testid=links-references]")
      .findAll("dt")
      .find((d) => d.text() === "compartment")!;
    await dt.trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      summaryOf(linkEntry("compartment"), "the link kind compartment"),
    );
  });

  it("opens the trigger, the priority and the delay of an event as elements of their own", () => {
    const event = constraintEvent.mainModel!.listOfEvents![0] as Event;
    const wrapper = mountWith(AttributesColumn, { element: event }, constraintEvent);
    const pks = wrapper.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain(event.trigger!.pk);
    expect(pks).toContain(event.priority!.pk);
    expect(pks).toContain(event.delay!.pk);
    // each of the three is an element of the index, so the link opens it
    for (const pk of [event.trigger!.pk, event.priority!.pk, event.delay!.pk]) {
      expect(constraintEvent.get(pk), pk).toBeDefined();
    }
  });

  it("shows the condition and the flags of a trigger", () => {
    const trigger = constraintEvent.mainModel!.listOfEvents![0]!.trigger!;
    const wrapper = mountWith(AttributesColumn, { element: trigger }, constraintEvent);
    const labels = wrapper.findAll("[data-testid=attribute-row] dt").map((dt) => dt.text());
    expect(labels).toEqual(["metaId", "sbo", "math", "initial value", "persistent"]);
    const rows = wrapper.findAll("[data-testid=attribute-row]");
    // initial value is false, persistent is true: the check mark is the mark of a true flag
    expect(rows[3]!.find("[aria-label=true]").exists()).toBe(false);
    expect(rows[4]!.find("[aria-label=true]").exists()).toBe(true);
  });

  it("renders the message of a constraint as the xhtml it is", () => {
    const constraint = constraintEvent.mainModel!.listOfConstraints![0] as Constraint;
    const wrapper = mountWith(AttributesColumn, { element: constraint }, constraintEvent);
    const message = wrapper.get("[data-testid=message]");
    expect(message.html()).toContain("<b>S1</b>");
    expect(message.text()).not.toContain("<message>");
  });

  it("lists the units of a unit definition next to its formula", () => {
    const definition = constraintEvent.mainModel!.listOfUnitDefinitions!.find(
      (u) => u.id === "mmole_per_min_l",
    ) as UnitDefinition;
    const wrapper = mountWith(AttributesColumn, { element: definition }, constraintEvent);
    const rows = wrapper.findAll("[data-testid=attribute-row]");
    expect(
      rows
        .find((r) => r.find("dt").text() === "formula")!
        .find("dd")
        .text(),
    ).not.toBe("-");
    const units = rows.find((r) => r.find("dt").text() === "units")!;
    expect(units.findAll("thead th").map((th) => th.text())).toEqual([
      "kind",
      "exponent",
      "scale",
      "multiplier",
    ]);
    expect(units.findAll("tbody tr").map((tr) => tr.findAll("td").map((td) => td.text()))).toEqual([
      ["mole", "1", "-3", "1"],
      ["second", "-1", "0", "60"],
      ["litre", "-1", "0", "1"],
    ]);
  });

  it("lists the reactants of a reaction with links to the species reference and the species", async () => {
    const reaction = repressilator.mainModel!.listOfReactions!.find(
      (r) => r.listOfReactants!.length > 0,
    ) as Reaction;
    const wrapper = mountWith(AttributesColumn, { element: reaction }, repressilator);
    const pks = wrapper.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain(reaction.listOfReactants![0]!.pk);
    const reactant = reaction.listOfReactants![0]!;
    expect(pks).toContain(repressilator.resolve(reactant.pk, "reactant", reactant.species));
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

  it("links the submodel of a replacement and the element inside it which it replaces", () => {
    const species = compDeletion.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(AttributesColumn, { element: species }, compDeletion);
    const row = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "replaced elements")!;
    const pks = row.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain("comp_deletion/Submodel:cell1");
    // the port of the submodel names the species, and the edge ends at that species
    expect(pks).toContain("cell/Species:glc");
  });

  it("shows the conversion factor and the deletion a replacement carries", () => {
    const species = compDeletion.mainModel!.listOfSpecies![0] as Species;
    const replaced = species.comp!.replacedElements![0]!;
    const rows = mountWith(ReplacedElementAttributes, { element: replaced }, compDeletion)
      .findAll("[data-testid=attribute-row]")
      .map((r) => [r.find("dt").text(), r.find("dd").text()]);
    expect(rows).toContainEqual(["submodel", "cell1"]);
    expect(rows).toContainEqual(["conversion factor", "f_amount"]);

    const parameter = compDeletion.mainModel!.listOfParameters!.find(
      (p) => p.comp?.replacedElements?.[0]?.deletion,
    )!;
    const scoped = parameter.comp!.replacedElements![0]!;
    const deletionRow = mountWith(ReplacedElementAttributes, { element: scoped }, compDeletion)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "deletion")!;
    expect(deletionRow.find("[data-testid=element-link]").attributes("data-pk")).toBe(
      "comp_deletion/Deletion:del_k",
    );
  });

  it("links every deletion of a submodel and the element it removes", () => {
    const submodel = compDeletion.mainModel!.listOfSubmodels![0] as Submodel;
    const wrapper = mountWith(SubmodelAttributes, { element: submodel }, compDeletion);
    const row = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "deletions")!;
    const pks = row.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain("comp_deletion/Deletion:del_k");
    expect(pks).toContain("cell/Parameter:k");
    expect(pks).toContain("cell/Reaction:sink");
  });

  it("renders the gene product association of a reaction as its tree", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const reaction = fbcConstraints.mainModel!.listOfReactions!.find((r) => r.id === "v1")!;
    const row = mountWith(ReactionAttributes, { element: reaction }, fbcConstraints)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "gene product association")!;
    // the structure of the tree, with the operators between the nodes of every group
    expect(row.find("dd").text()).toContain("((g_ptsG and g_ptsH) or g_galP)");
    const pks = row.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    // the association itself and one link per gene, resolved over the edge of its reference
    expect(pks).toEqual([
      "fbc_constraints_v3/GeneProductAssociation:gpa_v1",
      "fbc_constraints_v3/GeneProduct:g_ptsG",
      "fbc_constraints_v3/GeneProduct:g_ptsH",
      "fbc_constraints_v3/GeneProduct:g_galP",
    ]);
  });

  it("shows every node of an association tree in the inspector", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const or = fbcConstraints.get("fbc_constraints_v3/Or:gpa_v1.association")!;
    const wrapper = mountWith(AttributesColumn, { element: or }, fbcConstraints);
    expect(wrapper.text()).toContain("((g_ptsG and g_ptsH) or g_galP)");
    const ref = fbcConstraints.get("fbc_constraints_v3/GeneProductRef:ref_galP")!;
    const row = mountWith(AttributesColumn, { element: ref }, fbcConstraints)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "gene product")!;
    expect(row.find("[data-testid=element-link]").attributes("data-pk")).toBe(
      "fbc_constraints_v3/GeneProduct:g_galP",
    );
  });

  it("caps the nodes of one group of an association at the list limit", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const wide = {
      pk: "m/Or:wide",
      sbmlType: "Or",
      associations: Array.from({ length: LIST_LIMIT + 3 }, (_, k) => ({
        pk: `m/GeneProductRef:${k}`,
        sbmlType: "GeneProductRef",
        geneProduct: `g${k}`,
      })),
    };
    const wrapper = mountWith(GeneAssociationView, { node: wide }, fbcConstraints);
    expect(wrapper.text()).toContain(`g${LIST_LIMIT - 1}`);
    expect(wrapper.text()).not.toContain(`g${LIST_LIMIT}`);
    expect(wrapper.find("[data-testid=show-all]").text()).toBe("show all (3)");
    await wrapper.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.text()).toContain(`g${LIST_LIMIT + 2}`);
  });

  it("groups the links by kind in both directions", async () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(LinksColumn, { pk: species.pk }, repressilator);
    const references = wrapper.get("[data-testid=links-references]");
    expect(references.text()).toContain("compartment");
    const referencedBy = wrapper.get("[data-testid=links-referenced-by]");
    expect(referencedBy.findAll("[data-testid=element-link]").length).toBeGreaterThan(0);
  });

  it("names the species a reaction consumes and the reactions which consume a species", () => {
    const reaction = repressilator.mainModel!.listOfReactions![0]!;
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    // the graph runs from the reaction over its species reference to the species; the links of
    // the inspector ask over that hop, so neither side shows the reference in between
    const reactant = mountWith(LinksColumn, { pk: reaction.pk }, repressilator)
      .get("[data-testid=links-reactant]")
      .text();
    expect(reactant).toContain(reaction.listOfReactants![0]!.species);
    expect(reactant).not.toContain(".");

    const referencedBy = mountWith(LinksColumn, { pk: species.pk }, repressilator).get(
      "[data-testid=links-referenced-by]",
    );
    const reactions = new Set(
      repressilator.mainModel!.listOfReactions!.map((r) => r.id).filter((id) => id),
    );
    for (const link of referencedBy.findAll(
      "[data-testid=links-reactant] [data-testid=element-link]",
    ))
      expect(reactions).toContain(link.text());
  });

  it("shows none for an element without edges", () => {
    const wrapper = mountWith(LinksColumn, { pk: "nope" }, repressilator);
    expect(wrapper.text()).toContain("none");
  });

  it("shows the first 50 links of a group and the rest after show all, which then disappears", async () => {
    const pks = Array.from({ length: 60 }, (_, i) => `pk-${i}`);
    const wrapper = mountWith(LinksColumn, { pk: "root" }, fakeLinksIndex({ root: pks }));
    const references = wrapper.get("[data-testid=links-references]");
    expect(references.findAll("[data-testid=element-link]")).toHaveLength(50);
    await references.get("[data-testid=show-all]").trigger("click");
    expect(references.findAll("[data-testid=element-link]")).toHaveLength(60);
    expect(references.find("[data-testid=show-all]").exists()).toBe(false);
  });

  it("shows no show all button for a group of 50 or fewer links", () => {
    const pks = Array.from({ length: 50 }, (_, i) => `pk-${i}`);
    const wrapper = mountWith(LinksColumn, { pk: "root" }, fakeLinksIndex({ root: pks }));
    expect(wrapper.find("[data-testid=show-all]").exists()).toBe(false);
  });

  it("resets show all when another element of the same kind is selected", async () => {
    const index = fakeLinksIndex({
      a: Array.from({ length: 60 }, (_, i) => `a-${i}`),
      b: Array.from({ length: 60 }, (_, i) => `b-${i}`),
    });
    // mounted directly, not through `mountWith`, to keep the props typed for `setProps`
    const wrapper = mount(LinksColumn, {
      props: { pk: "a" },
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(index) },
      },
    });
    await wrapper.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.findAll("[data-testid=element-link]")).toHaveLength(60);

    await wrapper.setProps({ pk: "b" });
    expect(wrapper.findAll("[data-testid=element-link]")).toHaveLength(50);
    expect(wrapper.get("[data-testid=show-all]").text()).toBe("show all (10)");
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

  it("shows the reference of a replacedBy by unit ref when it names no port or id", () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const replaced: Species = {
      ...species,
      comp: {
        ...species.comp,
        replacedBy: {
          pk: "m/ReplacedBy:S1.replacedBy",
          sbmlType: "ReplacedBy",
          submodelRef: "submodel1",
          unitRef: "mmole",
        },
      },
    };
    const wrapper = mountWith(AttributesColumn, { element: replaced }, repressilator);
    const row = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "replaced by")!;
    expect(row.find("dd").text()).toContain("mmole");
  });

  it("closes the XML view again when another element is selected", async () => {
    const species = repressilator.mainModel!.listOfSpecies!;
    // mounted directly, not through `mountWith`, to keep the props typed for `setProps`
    const wrapper = mount(InspectorPanel, {
      props: { pk: species[0]!.pk },
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(repressilator) },
      },
    });
    await wrapper.get("[data-testid=inspector-xml-toggle]").trigger("click");
    expect(wrapper.find("[data-testid=xml-view]").exists()).toBe(true);
    await wrapper.setProps({ pk: species[1]!.pk });
    expect(wrapper.find("[data-testid=xml-view]").exists()).toBe(false);
    expect(wrapper.get("[data-testid=inspector-id]").text()).toBe(species[1]!.id);
  });

  it("shows the annotation element of the model in the place of its xml", async () => {
    const model = constraintEvent.mainModel!;
    const wrapper = mount(InspectorPanel, {
      props: { pk: model.pk },
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(constraintEvent) },
      },
    });
    await wrapper.get("[data-testid=inspector-xml-toggle]").trigger("click");
    const view = wrapper.get("[data-testid=xml-view]");
    expect(wrapper.get("[data-testid=xml-caption]").text()).toBe(
      "The annotation element of the model.",
    );
    expect(view.get("pre").text()).toContain("sbml4humans:model");
    // the annotation element, not the model element
    expect(view.get("pre").text()).not.toContain("<listOfSpecies>");
  });

  it("says that a document without an annotation carries none", async () => {
    const wrapper = mount(InspectorPanel, {
      props: { pk: repressilator.document.pk },
      global: {
        plugins: [router],
        directives: { tooltip: vTooltip },
        provide: { [ReportIndexKey as symbol]: ref(repressilator) },
      },
    });
    await wrapper.get("[data-testid=inspector-xml-toggle]").trigger("click");
    expect(wrapper.get("[data-testid=xml-view]").text()).toContain(
      "The document carries no annotation",
    );
  });

  it("renders the header of the panel", async () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(InspectorPanel, { pk: species.pk }, repressilator);
    expect(wrapper.get("[data-testid=inspector-type]").text()).toBe("Species");
    expect(wrapper.get("[data-testid=inspector-id]").text()).toBe(species.id);
    expect(wrapper.find("[data-testid=inspector-close]").exists()).toBe(true);
  });

  it("links the type of the header to its reference page", async () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(InspectorPanel, { pk: species.pk }, repressilator);
    const link = wrapper.get("[data-testid=inspector-type-link]");
    expect(link.attributes("href")).toBe(referenceUrl("Species"));
    expect(link.attributes("target")).toBe("_blank");
    expect(link.attributes("rel")).toBe("noopener");
    expect(link.get("svg").classes()).toContain("lucide-external-link");
    expect(link.get("[data-testid=inspector-type]").text()).toBe("Species");
  });

  const COLUMNS = [{ key: "id", header: "id" }];
  const rowsOf = (n: number, prefix: string) =>
    Array.from({ length: n }, (_, i) => ({ id: `${prefix}${i}` }));
  const mountTable = (rows: { id: string }[]) =>
    mount(NestedTable, {
      props: { rows, columns: COLUMNS },
      global: { directives: { tooltip: vTooltip } },
    });

  it("shows the first 50 rows of a nested table and the rest after show all, which then disappears", async () => {
    const wrapper = mountTable(rowsOf(60, "r"));
    expect(wrapper.findAll("tbody tr")).toHaveLength(50);
    await wrapper.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.findAll("tbody tr")).toHaveLength(60);
    expect(wrapper.find("[data-testid=show-all]").exists()).toBe(false);
  });

  it("shows no show all button for a nested table of 50 or fewer rows", () => {
    const wrapper = mountTable(rowsOf(50, "r"));
    expect(wrapper.find("[data-testid=show-all]").exists()).toBe(false);
  });

  it("resets show all when the rows change to another element's rows", async () => {
    const wrapper = mountTable(rowsOf(60, "a"));
    await wrapper.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.findAll("tbody tr")).toHaveLength(60);

    await wrapper.setProps({ rows: rowsOf(60, "b") });
    expect(wrapper.findAll("tbody tr")).toHaveLength(50);
    expect(wrapper.get("[data-testid=show-all]").text()).toBe("show all (10)");
  });
});
