import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { ref } from "vue";

import type {
  Constraint,
  Event,
  QualitativeSpecies,
  Reaction,
  SBase,
  Species,
  Submodel,
  Transition,
  Uncertainty,
  UnitDefinition,
} from "@/api/types";
import AttributesColumn from "@/components/inspector/AttributesColumn.vue";
import InspectorPanel from "@/components/inspector/InspectorPanel.vue";
import LinksColumn from "@/components/inspector/LinksColumn.vue";
import NestedTable from "@/components/inspector/NestedTable.vue";
import GeneAssociationView from "@/components/misc/GeneAssociationView.vue";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import ExternalModelDefinitionAttributes from "@/components/inspector/attributes/ExternalModelDefinitionAttributes.vue";
import ListOfAttributes from "@/components/inspector/attributes/ListOfAttributes.vue";
import ReactionAttributes from "@/components/inspector/attributes/ReactionAttributes.vue";
import ReplacedElementAttributes from "@/components/inspector/attributes/ReplacedElementAttributes.vue";
import QualitativeSpeciesAttributes from "@/components/inspector/attributes/QualitativeSpeciesAttributes.vue";
import SubmodelAttributes from "@/components/inspector/attributes/SubmodelAttributes.vue";
import TransitionAttributes from "@/components/inspector/attributes/TransitionAttributes.vue";
import UncertaintyAttributes from "@/components/inspector/attributes/UncertaintyAttributes.vue";
import { ELEMENT_TYPES, DOCUMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { vTooltip } from "@/directives/tooltip";
import { ReportIndexKey } from "@/report/context";
import { attributeEntry, linkEntry, referenceUrl } from "@/report/glossary";
import { ASSOCIATION_LIMIT } from "@/report/geneAssociation";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadFixture, loadReport } from "./fixtures";
import { summaryOf } from "./summary";

const fixtures = [
  "repressilator",
  "icg_body",
  "fbc_example",
  "distrib_uncertainties",
  "model_definitions",
  "list_of",
] as const;
const indexes = fixtures.map((name) => new ReportIndex(loadReport(name)));
const repressilator = indexes[0]!;
const constraintEvent = new ReportIndex(loadReport("constraint_event"));
const compDeletion = new ReportIndex(loadReport("comp_deletion"));
const fbcConstraints = new ReportIndex(loadReport("fbc_constraints_v3"));
const fbcBounds = new ReportIndex(loadReport("fbc_bounds_v1"));
const qual = new ReportIndex(loadReport("qual_example"));
const distribSpans = new ReportIndex(loadReport("distrib_spans"));
const listOf = new ReportIndex(loadReport("list_of"));

/** A minimal index for the links list size tests: one "compartment" edge per target pk out of
 * the given source, nothing else, so the numbers stay exact and independent of the fixtures. */
function fakeLinksIndex(bySource: Record<string, string[]>): ReportIndex {
  const index = {
    references: (pk: string) =>
      (bySource[pk] ?? []).map((target) => ({ source: pk, target, kind: "compartment" as const })),
    referencedBy: () => [],
    referencesAcross: () => [],
    referencedAcross: () => [],
    entry: () => index,
    get: (pk: string) => ({ pk, id: pk, metaId: null, sbmlType: undefined }),
  } as unknown as ReportIndex;
  return index;
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

  it("lists no package for a Level 3 Version 2 document of core alone", () => {
    const wrapper = mountWith(
      AttributesColumn,
      { element: constraintEvent.document },
      constraintEvent,
    );
    const packages = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((row) => row.find("dt").text() === "packages")!;
    expect(packages.find("dd").text()).toBe("-");
  });

  it("lists every package of a document with its version", () => {
    const wrapper = mountWith(AttributesColumn, { element: qual.document }, qual);
    const packages = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((row) => row.find("dt").text() === "packages")!;
    expect(packages.find("dd").text()).toBe("qual v1");
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
    expect(labels).toEqual(["metaid", "sboTerm", "math", "initialValue", "persistent"]);
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
    const units = rows.find((r) => r.find("dt").text() === "listOfUnits")!;
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
    // the reference carries no id: its row names it as every link does, as the name the report
    // gives it and not as the id of its species
    const table = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((row) => row.find("dt").text() === "listOfReactants")!;
    const name = table.get("tbody tr td [data-testid=report-name]");
    expect(name.text()).toBe(`${reaction.id}.${reactant.species}`);
  });

  it("names a nested element in its row as every link to it names it", () => {
    // a kinetic law, a trigger and an association without an id were a generic word in their
    // row, which repeated the label of the row and differed from the link
    const reaction = constraintEvent.mainModel!.listOfReactions!.find((r) => r.id === "R1")!;
    const rows = mountWith(AttributesColumn, { element: reaction }, constraintEvent)
      .findAll("[data-testid=attribute-row]")
      .filter((r) => r.find("dd [data-testid=element-link]").exists())
      .map((r) => [r.find("dt").text(), r.find("dd [data-testid=element-link]").text()]);
    expect(rows).toContainEqual(["kineticLaw", "R1.kineticLaw"]);
    const v2 = fbcConstraints.mainModel!.listOfReactions!.find((r) => r.id === "v2")!;
    const association = mountWith(AttributesColumn, { element: v2 }, fbcConstraints)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "fbc:geneProductAssociation")!;
    expect(association.find("[data-testid=element-link]").text()).toBe("v2.geneProductAssociation");
    const objective = fbcBounds.mainModel!.listOfObjectives!.find((o) => o.id === "biomass_max")!;
    const term = mountWith(AttributesColumn, { element: objective }, fbcBounds).get(
      "[data-testid=nested-table] tbody tr td",
    );
    expect(term.text()).toBe("biomass_max.EX_biomass");
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
      .find((r) => r.find("dt").text() === "timeConversionFactor")!;
    expect(row.find("a").exists()).toBe(false);
    expect(row.find("dd").text()).toBe("-");
  });

  it("links the submodel of a replacement and the element inside it which it replaces", () => {
    const species = compDeletion.mainModel!.listOfSpecies![0] as Species;
    const wrapper = mountWith(AttributesColumn, { element: species }, compDeletion);
    const row = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "comp:listOfReplacedElements")!;
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
    expect(rows).toContainEqual(["submodelRef", "cell1"]);
    expect(rows).toContainEqual(["conversionFactor", "f_amount"]);

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
      .find((r) => r.find("dt").text() === "listOfDeletions")!;
    const pks = row.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain("comp_deletion/Deletion:del_k");
    expect(pks).toContain("cell/Parameter:k");
    expect(pks).toContain("cell/Reaction:sink");
  });

  it("shows the flux bound of a Version 1 model with the reaction it constrains", async () => {
    await router.push("/examples/fbc_bounds_v1");
    const bound = fbcBounds.mainModel!.listOfFluxBounds![0]!;
    const rows = mountWith(AttributesColumn, { element: bound }, fbcBounds)
      .findAll("[data-testid=attribute-row]")
      .map((r) => [r.find("dt").text(), r.find("dd").text()]);
    expect(rows).toContainEqual(["reaction", "v1"]);
    expect(rows).toContainEqual(["operation", "greaterEqual"]);
    expect(rows).toContainEqual(["value", "0"]);
  });

  it("shows the strictness of a model and links its active objective", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const row = mountWith(AttributesColumn, { element: fbcConstraints.mainModel! }, fbcConstraints)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "fbc:activeObjective")!;
    expect(row.find("[data-testid=element-link]").attributes("data-pk")).toBe(
      "fbc_constraints_v3/Objective:growth_max",
    );
  });

  it("links both reactions of a quadratic flux objective", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const objective = fbcConstraints.mainModel!.listOfObjectives!.find(
      (o) => o.id === "uptake_min",
    )!;
    const wrapper = mountWith(AttributesColumn, { element: objective }, fbcConstraints);
    const pks = wrapper.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain("fbc_constraints_v3/FluxObjective:fo_uptake");
    expect(pks).toContain("fbc_constraints_v3/Reaction:v1");
    expect(pks).toContain("fbc_constraints_v3/Reaction:v2");
    expect(wrapper.text()).toContain("quadratic");
  });

  it("links the variables and the coefficient of a user defined constraint", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const constraint = fbcConstraints.mainModel!.listOfUserDefinedConstraints![0]!;
    const wrapper = mountWith(AttributesColumn, { element: constraint }, fbcConstraints);
    const rows = wrapper
      .findAll("[data-testid=attribute-row]")
      .map((r) => [r.find("dt").text(), r.find("dd").text()]);
    expect(rows).toContainEqual(["lowerBound", "ratio_lb"]);
    expect(rows).toContainEqual(["upperBound", "ratio_ub"]);
    const pks = wrapper.findAll("[data-testid=element-link]").map((l) => l.attributes("data-pk"));
    expect(pks).toContain("fbc_constraints_v3/Reaction:v1");
    expect(pks).toContain("fbc_constraints_v3/Parameter:c_two");
    expect(pks).toContain("fbc_constraints_v3/UserDefinedConstraintComponent:ratio_v1");
  });

  it("shows the key value pairs of an element", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const parameter = fbcConstraints.mainModel!.listOfParameters!.find(
      (p) => p.id === "maintenance",
    )!;
    const row = mountWith(AttributesColumn, { element: parameter }, fbcConstraints)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "fbc:listOfKeyValuePairs")!;
    expect(row.find("dd").text()).toContain("source");
    expect(row.find("dd").text()).toContain("measured");
    expect(row.find("dd").find("a").attributes("href")).toBe("https://sbml.org/fbc/keyvaluepair");

    // the value of a pair is text, which reads as the word it is and not as a number
    const infinite = { ...parameter, keyValuePairs: [{ key: "bound", value: "Infinity" }] };
    const text = mountWith(AttributesColumn, { element: infinite }, fbcConstraints)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "fbc:listOfKeyValuePairs")!
      .find("tbody")
      .text();
    expect(text).toContain("Infinity");
    expect(text).not.toContain("\u221e");
  });

  it("renders the gene product association of a reaction as its tree", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const reaction = fbcConstraints.mainModel!.listOfReactions!.find((r) => r.id === "v1")!;
    const row = mountWith(ReactionAttributes, { element: reaction }, fbcConstraints)
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.find("dt").text() === "fbc:geneProductAssociation")!;
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
      .find((r) => r.find("dt").text() === "geneProduct")!;
    expect(row.find("[data-testid=element-link]").attributes("data-pk")).toBe(
      "fbc_constraints_v3/GeneProduct:g_galP",
    );
  });

  it("caps the nodes of one group of an association", async () => {
    await router.push("/examples/fbc_constraints_v3");
    const wide = {
      pk: "m/Or:wide",
      sbmlType: "Or",
      associations: Array.from({ length: ASSOCIATION_LIMIT + 3 }, (_, k) => ({
        pk: `m/GeneProductRef:${k}`,
        sbmlType: "GeneProductRef",
        geneProduct: `g${k}`,
      })),
    };
    const wrapper = mountWith(GeneAssociationView, { node: wide }, fbcConstraints);
    expect(wrapper.text()).toContain(`g${ASSOCIATION_LIMIT - 1}`);
    expect(wrapper.text()).not.toContain(`g${ASSOCIATION_LIMIT}`);
    expect(wrapper.find("[data-testid=show-all]").text()).toBe("show all (3)");
    await wrapper.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.text()).toContain(`g${ASSOCIATION_LIMIT + 2}`);
  });

  it("opens an association deeper than two operator levels one level at a time", async () => {
    await router.push("/examples/fbc_constraints_v3");
    // five operator levels, every one with a gene of its own next to the level below it, the
    // shape which keeps an association of Recon3D walkable
    const gene = (name: string) => ({
      pk: `m/GeneProductRef:${name}`,
      sbmlType: "GeneProductRef",
      geneProduct: name,
    });
    let deep: Record<string, unknown> = gene("leaf");
    for (let level = 4; level >= 0; level--) {
      const sbmlType = level % 2 === 0 ? "Or" : "And";
      deep = { pk: `m/${sbmlType}:${level}`, sbmlType, associations: [deep, gene(`g${level}`)] };
    }
    const wrapper = mountWith(GeneAssociationView, { node: deep }, fbcConstraints);
    const open = () => wrapper.findAll("[data-testid=gene-association-open]");
    expect(wrapper.text()).toContain("g1");
    expect(wrapper.text()).not.toContain("g2");
    expect(open().map((button) => button.text())).toEqual(["(or of 2)"]);

    // the level below it holds genes only, two of them, which are written out: the button would
    // take the width of the two genes and hide them
    await open()[0]!.trigger("click");
    expect(wrapper.text()).toContain("g3");
    expect(wrapper.text()).toContain("(leaf or g4)");
    expect(open()).toHaveLength(0);
  });

  it("writes out a deep group of a few genes and opens a deep group of more on a click", () => {
    const gene = (name: string) => ({
      pk: `m/GeneProductRef:${name}`,
      sbmlType: "GeneProductRef",
      geneProduct: name,
    });
    const group = (name: string, genes: string[]) => ({
      pk: `m/And:${name}`,
      sbmlType: "And",
      associations: genes.map(gene),
    });
    const tree = {
      pk: "m/Or:root",
      sbmlType: "Or",
      associations: [
        {
          pk: "m/And:middle",
          sbmlType: "And",
          associations: [group("few", ["a", "b"]), group("many", ["c", "d", "e", "f"])],
        },
      ],
    };
    const wrapper = mountWith(GeneAssociationView, { node: tree }, fbcConstraints);
    expect(wrapper.text()).toContain("(a and b)");
    // the button is its text, without the spaces a template would leave around it
    expect(
      wrapper
        .findAll("[data-testid=gene-association-open]")
        .map((button) => button.element.textContent),
    ).toEqual(["(and of 4)"]);
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

  it("names the reactions whose kinetic law reads a species and what the law of a reaction reads", () => {
    const model = repressilator.mainModel!;
    const species = model.listOfSpecies!.find((s) => s.id === "PX")!;
    // the kinetic laws of the repressilator are keyed by their meta id; the math of a kinetic law
    // is the speed of its reaction, so the links of a species name the reaction and not the law
    const math = mountWith(LinksColumn, { pk: species.pk }, repressilator)
      .get("[data-testid=links-referenced-by] [data-testid=links-math]")
      .findAll("[data-testid=element-link]");
    expect(math.map((link) => link.text())).toEqual(["Reaction7", "Reaction11"]);
    for (const link of math) {
      expect(repressilator.get(link.attributes("data-pk")!)?.sbmlType).toBe("Reaction");
    }

    // the reaction names its kinetic law after itself and lists what the law reads as its math
    const reaction = model.listOfReactions!.find((r) => r.id === "Reaction7")!;
    const links = mountWith(LinksColumn, { pk: reaction.pk }, repressilator).get(
      "[data-testid=links-references]",
    );
    expect(links.get("[data-testid=links-kineticLaw]").text()).toContain("Reaction7.kineticLaw");
    expect(
      links
        .get("[data-testid=links-math]")
        .findAll("[data-testid=element-link]")
        .map((link) => link.text()),
    ).toContain("PX");

    // the kinetic law keeps its own links: its math and the reaction which names it
    const law = mountWith(LinksColumn, { pk: reaction.kineticLaw!.pk }, repressilator);
    expect(law.get("[data-testid=links-references] [data-testid=links-math]").text()).toContain(
      "PX",
    );
    expect(
      law.get("[data-testid=links-referenced-by] [data-testid=links-kineticLaw]").text(),
    ).toContain("Reaction7");
  });

  it("names the transition whose function terms read a qualitative species", () => {
    const species = qual.mainModel!.listOfQualitativeSpecies!.find((s) => s.id === "S")!;
    const math = mountWith(LinksColumn, { pk: species.pk }, qual).get(
      "[data-testid=links-referenced-by] [data-testid=links-math]",
    );
    expect(math.findAll("[data-testid=element-link]").map((link) => link.text())).toEqual(["tr_G"]);

    const transition = qual.mainModel!.listOfTransitions!.find((t) => t.id === "tr_G")!;
    const references = mountWith(LinksColumn, { pk: transition.pk }, qual).get(
      "[data-testid=links-references]",
    );
    const read = references
      .get("[data-testid=links-math]")
      .findAll("[data-testid=element-link]")
      .map((link) => link.text());
    expect(read).toEqual(expect.arrayContaining(["S", "P", "theta_G_S", "theta_G_P"]));
    // the terms themselves stay links of the transition
    expect(references.get("[data-testid=links-functionTerm]").text()).toContain(
      "tr_G.functionTerm.0",
    );
  });

  it("names the reactions a gene product is needed by and the genes a reaction needs", () => {
    // the graph runs from the reaction over its association tree to a reference of the gene
    // product; the links of the inspector ask over those steps, the way they ask over a species
    // reference, so a gene product lists its reactions and not the references which name it
    const model = fbcConstraints.mainModel!;
    const product = model.listOfGeneProducts!.find((g) => g.id === "g_galP")!;
    const group = mountWith(LinksColumn, { pk: product.pk }, fbcConstraints).get(
      "[data-testid=links-referenced-by] [data-testid=links-geneProduct]",
    );
    const links = group.findAll("[data-testid=element-link]");
    expect(links.map((link) => link.text())).toEqual(["v1", "v2"]);
    for (const link of links) {
      expect(fbcConstraints.get(link.attributes("data-pk")!)?.sbmlType).toBe("Reaction");
    }

    const reaction = model.listOfReactions!.find((r) => r.id === "v1")!;
    const references = mountWith(LinksColumn, { pk: reaction.pk }, fbcConstraints).get(
      "[data-testid=links-references]",
    );
    expect(
      references
        .get("[data-testid=links-geneProduct]")
        .findAll("[data-testid=element-link]")
        .map((link) => link.text()),
    ).toEqual(["g_ptsG", "g_ptsH", "g_galP"]);
    // the association stays a link of the reaction, and its nodes keep their own links
    expect(references.get("[data-testid=links-geneProductAssociation]").text()).toContain("gpa_v1");
    const leaf = mountWith(
      LinksColumn,
      { pk: "fbc_constraints_v3/GeneProductRef:ref_galP" },
      fbcConstraints,
    );
    expect(
      leaf
        .get("[data-testid=links-references] [data-testid=links-geneProduct]")
        .findAll("[data-testid=element-link]")
        .map((link) => link.text()),
    ).toEqual(["g_galP"]);
  });

  it("names a flux objective so that it does not read as the reaction it weighs", () => {
    const reaction = fbcBounds.mainModel!.listOfReactions!.find((r) => r.id === "EX_biomass")!;
    const group = mountWith(LinksColumn, { pk: reaction.pk }, fbcBounds).get(
      "[data-testid=links-referenced-by] [data-testid=links-fluxObjective]",
    );
    expect(group.findAll("[data-testid=element-link]").map((link) => link.text())).toEqual([
      "biomass_max.EX_biomass",
    ]);
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

  it("shows the measures of every uncertainty of an element in its inspector", () => {
    // how well a value is known is shown where the value is, not one click away
    const km = distribSpans.mainModel!.listOfParameters!.find((p) => p.id === "Km")!;
    const wrapper = mountWith(AttributesColumn, { element: km }, distribSpans);
    const blocks = wrapper.findAll("[data-testid=uncertainty]");
    expect(blocks).toHaveLength(2);
    const [purified, lysate] = blocks;
    expect(purified!.get("[data-testid=element-link]").attributes("data-pk")).toBe(
      "distrib_spans/Uncertainty:u_Km_purified",
    );
    expect(purified!.text()).toContain("Wilson 1997, purified enzyme");
    expect(purified!.findAll("[data-testid=uncert-measure]")).toHaveLength(4);
    expect(purified!.findAll("[data-testid=uncert-value]").map((v) => v.text())).toEqual([
      "0.5",
      "0.06",
      "12",
      "0.38 to 0.63",
    ]);
    expect(lysate!.text()).toContain("Baker 2012, cell lysate");
    expect(lysate!.get("[data-testid=uncert-span]").text()).toBe("Km_lower to Km_upper");
    // the count of the measures is gone, the measures are there
    expect(wrapper.text()).not.toContain("parameters");
  });

  it("shows the value and the math of an external parameter which carries both", () => {
    // distrib §3.11 lets an external parameter be a value, a span, a math or any combination
    const distrib = distribSpans;
    const uncertainty = [...distrib.elements.values()].find(
      (element) => element.sbmlType === "Uncertainty",
    ) as Uncertainty;
    const both: Uncertainty = {
      ...uncertainty,
      uncertParameters: [
        {
          pk: "both/UncertParameter:both",
          sbmlType: "UncertParameter",
          type: "externalParameter",
          value: 7,
          math: { latex: "k", formula: "k" },
          var: null,
          units: null,
          definitionUrl: null,
        },
      ],
    };
    const value = mountWith(UncertaintyAttributes, { element: both }, distrib).get(
      "[data-testid=uncert-value]",
    );
    expect(value.text()).toContain("7");
    expect(value.find(".katex").exists()).toBe(true);
  });

  it("lets an uncertainty name the element whose value it describes", () => {
    const uncertainty = "distrib_spans/Uncertainty:u_Km_lysate";
    const links = mountWith(LinksColumn, { pk: uncertainty }, distribSpans).get(
      "[data-testid=links-referenced-by] [data-testid=links-uncertainty]",
    );
    expect(links.findAll("[data-testid=element-link]").map((link) => link.text())).toEqual(["Km"]);
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
          pk: "unsafe/UncertParameter:unsafe",
          sbmlType: "UncertParameter",
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

  it("shows a span as the interval it is and links the ends it names", async () => {
    await router.push("/examples/distrib_spans");
    const km = distribSpans.mainModel!.listOfParameters!.find((p) => p.id === "Km")!;
    const byValues = km.uncertainties![0] as Uncertainty;
    const rows = mountWith(UncertaintyAttributes, { element: byValues }, distribSpans)
      .findAll("[data-testid=uncert-value]")
      .map((cell) => cell.text().replace(/\s+/g, " "));
    // the range of the measurement reads as the interval the file writes, where the report
    // used to show the word "range" and five empty cells
    expect(rows).toEqual(["0.5", "0.06", "12", "0.38 to 0.63"]);

    const byReference = km.uncertainties![1] as Uncertainty;
    const wrapper = mountWith(UncertaintyAttributes, { element: byReference }, distribSpans);
    const span = wrapper.get("[data-testid=uncert-span]");
    expect(span.text().replace(/\s+/g, " ")).toBe("Km_lower to Km_upper");
    expect(
      span.findAll("[data-testid=element-link]").map((link) => link.attributes("data-pk")),
    ).toEqual(["distrib_spans/Parameter:Km_lower", "distrib_spans/Parameter:Km_upper"]);
  });

  it("shows the parameters of a distribution under the parameter they define", async () => {
    await router.push("/examples/distrib_spans");
    const vmax = distribSpans.mainModel!.listOfParameters!.find((p) => p.id === "Vmax")!;
    const wrapper = mountWith(
      UncertaintyAttributes,
      { element: vmax.uncertainties![0] as Uncertainty },
      distribSpans,
    );
    const measures = wrapper
      .findAll("[data-testid=uncert-measure]")
      .map((cell) => cell.get("[data-testid=element-link]").text());
    expect(measures).toEqual(["Vmax_mean_measure", "Vmax_distribution", "Vmax_alpha", "Vmax_beta"]);
    // the type stays next to an identifier, because the identifier does not say what the
    // measure is
    expect(wrapper.findAll("[data-testid=uncert-type]").map((cell) => cell.text())).toEqual([
      "mean",
      "distribution",
      "externalParameter",
      "externalParameter",
    ]);
    // the two parameters of the distribution are indented below it
    const depths = wrapper
      .findAll("[data-testid=uncert-measure]")
      .map((cell) => cell.attributes("data-depth"));
    expect(depths).toEqual(["0", "0", "1", "1"]);
    // the mean of the maximal rate is not a number but the parameter which holds it
    expect(wrapper.findAll("[data-testid=uncert-value]")[0]!.text()).toBe("Vmax_mean");
  });

  it("shows the attributes of an uncert parameter and of a span", async () => {
    await router.push("/examples/distrib_spans");
    const km = distribSpans.mainModel!.listOfParameters!.find((p) => p.id === "Km")!;
    const mean = km.uncertainties![0]!.uncertParameters![0]!;
    const meanRows = mountWith(AttributesColumn, { element: mean }, distribSpans)
      .findAll("[data-testid=attribute-row]")
      .map((row) => row.get("dt").text());
    expect(meanRows).toContain("type");
    expect(meanRows).toContain("value");
    expect(meanRows).toContain("units");

    const span = km.uncertainties![1]!.uncertParameters![1]!;
    const spanWrapper = mountWith(AttributesColumn, { element: span }, distribSpans);
    const spanRows = spanWrapper
      .findAll("[data-testid=attribute-row]")
      .map((row) => row.get("dt").text());
    expect(spanRows).toContain("interval");
    expect(spanWrapper.get("[data-testid=uncert-span]").text().replace(/\s+/g, " ")).toBe(
      "Km_lower to Km_upper",
    );
  });

  it("shows the levels of a qualitative species with a link to its compartment", async () => {
    await router.push("/examples/qual_example");
    const signal = qual.mainModel!.listOfQualitativeSpecies![0] as QualitativeSpecies;
    const wrapper = mountWith(QualitativeSpeciesAttributes, { element: signal }, qual);
    const rows = wrapper.findAll("[data-testid=attribute-row]").map((r) => r.get("dt").text());
    expect(rows).toEqual(["compartment", "initialLevel", "maxLevel", "constant"]);
    expect(wrapper.find("[data-testid=element-link]").text()).toBe("cell");
    // the level the file does not set reads as a dash and not as the integer libsbml answers
    const initial = wrapper
      .findAll("[data-testid=attribute-row]")
      .find((r) => r.get("dt").text() === "initialLevel")!;
    expect(initial.get("dd").text()).toBe("-");
  });

  it("shows the function terms of a transition as its transition table", async () => {
    await router.push("/examples/qual_example");
    const transition = qual.mainModel!.listOfTransitions![0] as Transition;
    const wrapper = mountWith(TransitionAttributes, { element: transition }, qual);
    const tables = wrapper.findAllComponents(NestedTable);
    expect(tables).toHaveLength(3);

    // the inputs with the species they read and the sign of their influence
    const inputs = tables[0]!;
    expect(inputs.findAll("thead th:not([aria-hidden])").map((th) => th.text())).toEqual([
      "id",
      "qualitativeSpecies",
      "sign",
      "thresholdLevel",
      "transitionEffect",
    ]);
    expect(inputs.findAll("tbody tr")).toHaveLength(3);
    expect(inputs.findAll("[data-testid=qual-sign]").map((s) => s.text())).toEqual([
      "+",
      "\u2212",
      "+",
    ]);

    // the terms in the order in which they are read, the default term as the last row
    const terms = tables[2]!;
    expect(terms.findAll("thead th").map((th) => th.text())).toEqual([
      "term",
      "math",
      "resultLevel",
    ]);
    const rows = terms.findAll("tbody tr");
    expect(rows).toHaveLength(3);
    expect(rows[2]!.text()).toContain("otherwise");
    expect(rows[2]!.findAll("td")[2]!.text()).toBe("0");
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
      .find((r) => r.find("dt").text() === "comp:replacedBy")!;
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

  describe("the lists which state something of their own", () => {
    const model = listOf.mainModel!;
    const reaction = model.listOfReactions![0]!;
    const unitDefinition = model.listOfUnitDefinitions![0]!;

    /** The names of the links of the row of the lists, null for an element without the row. */
    function listsRow(element: SBase): string[] | null {
      const wrapper = mountWith(AttributesColumn, { element }, listOf);
      const row = wrapper
        .findAll("[data-testid=attribute-row]")
        .find((r) => r.get("dt").text() === "lists");
      return row?.findAll("[data-testid=element-link]").map((link) => link.text()) ?? null;
    }

    it("links the lists of an element from its attributes", async () => {
      await router.push("/examples/list_of");
      // the empty list of rules has no table, so the model is where a reader finds it
      expect(listsRow(model)).toEqual(["listOfUnitDefinitions", "metabolites", "listOfRules"]);
      expect(listsRow(reaction)).toEqual(["J0.listOfReactants"]);
      expect(listsRow(unitDefinition)).toEqual(["per_second.listOfUnits"]);
    });

    it("links a list by its pk with the mark of its type", async () => {
      await router.push("/examples/list_of");
      const wrapper = mountWith(AttributesColumn, { element: reaction }, listOf);
      const link = wrapper.get("[data-testid=lists] [data-testid=element-link]");
      expect(link.attributes("data-pk")).toBe(reaction.lists![0]!.pk);
      expect(link.get("[data-testid=type-mark]").attributes("aria-label")).toBe("ListOf");
      // the list has no id, the name the report gives it is set apart from one
      expect(link.find("[data-testid=report-name]").exists()).toBe(true);
    });

    it("has no row of lists for an element without one", () => {
      expect(listsRow(model.listOfSpecies![0]!)).toBeNull();
      expect(listsRow(listOf.document)).toBeNull();
      expect(listsRow(listOf.list(model.pk, "listOfSpecies")!)).toBeNull();
    });

    it("shows the name a list has in the file and the number of its elements", () => {
      const rows = (element: string) =>
        mountWith(ListOfAttributes, { element: listOf.list(model.pk, element)! }, listOf)
          .findAll("[data-testid=attribute-row]")
          .map((row) => [row.get("dt").text(), row.get("dd").text()]);
      expect(rows("listOfSpecies")).toEqual([
        ["list", "listOfSpecies"],
        ["size", "2"],
      ]);
      expect(rows("listOfRules")).toEqual([
        ["list", "listOfRules"],
        ["size", "0"],
      ]);
    });

    it("shows a list in the inspector with its notes and the xml without its elements", async () => {
      const species = listOf.list(model.pk, "listOfSpecies")!;
      const wrapper = mountWith(InspectorPanel, { pk: species.pk }, listOf);
      expect(wrapper.get("[data-testid=inspector-type]").text()).toBe("ListOf");
      expect(wrapper.get("[data-testid=inspector-id]").text()).toBe("metabolites");
      expect(wrapper.get("[data-testid=inspector-name]").text()).toBe(species.name);
      expect(wrapper.get("[data-testid=inspector-type-link]").attributes("href")).toBe(
        referenceUrl("ListOf"),
      );
      expect(wrapper.text()).toContain("The species of this list are the two metabolites");
      await wrapper.get("[data-testid=inspector-xml-toggle]").trigger("click");
      const xml = wrapper.get("[data-testid=xml-view] pre").text();
      expect(xml).toContain("<listOfSpecies");
      expect(xml).toContain("bqbiol:isPartOf");
      expect(xml).not.toContain("<species");
    });
  });

  const COLUMNS = [{ key: "id", header: "id" }];
  const rowsOf = (n: number, prefix: string) =>
    Array.from({ length: n }, (_, i) => ({ id: `${prefix}${i}` }));
  const mountTable = (rows: { id: string }[]) =>
    mount(NestedTable, {
      props: { rows, columns: COLUMNS },
      global: { directives: { tooltip: vTooltip } },
    });

  it("explains every header of a nested table on hover", async () => {
    // the headers of the tables of an input, an output and a measure explained nothing
    const transition = qual.mainModel!.listOfTransitions!.find((t) => t.id === "tr_G")!;
    const wrapper = mountWith(TransitionAttributes, { element: transition }, qual);
    const headers = wrapper.findAll("[data-testid=nested-table] thead th");
    const sign = headers.find((th) => th.text() === "sign")!;
    await sign.get("span").trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      `sign: ${attributeEntry("Input", "sign")!.summary}`,
    );
    const level = headers.find((th) => th.text() === "outputLevel")!;
    await level.get("span").trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      `outputLevel: ${attributeEntry("Output", "outputLevel")!.summary}`,
    );
    wrapper.unmount();
  });

  it("gives the columns of the tables one element shows in a row the same widths", () => {
    // the reactants and the products of a reaction, and the inputs and the outputs of a
    // transition, each sized their columns on their own, so that "species" jumped between two
    // tables stacked under each other
    const widths = (wrapper: ReturnType<typeof mountWith>) =>
      wrapper
        .findAll("[data-testid=nested-table]")
        .map((table) => table.findAll("col").map((col) => col.attributes("style") ?? ""));
    const reaction = constraintEvent.mainModel!.listOfReactions!.find((r) => r.id === "R1")!;
    const [reactants, products] = widths(
      mountWith(ReactionAttributes, { element: reaction }, constraintEvent),
    );
    expect(reactants!.slice(0, 3).every((style) => style.includes("width"))).toBe(true);
    expect(reactants).toEqual(products);

    const transition = qual.mainModel!.listOfTransitions!.find((t) => t.id === "tr_G")!;
    const [inputs, outputs] = widths(
      mountWith(TransitionAttributes, { element: transition }, qual),
    );
    expect(inputs!.slice(0, 2)).toEqual(outputs!.slice(0, 2));
    expect(inputs![1]).toContain("width");

    const km = distribSpans.mainModel!.listOfParameters!.find((p) => p.id === "Km")!;
    const [purified, lysate] = widths(mountWith(AttributesColumn, { element: km }, distribSpans));
    expect(purified!.slice(0, 3)).toEqual(lysate!.slice(0, 3));
    expect(purified![0]).toContain("width");
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

  describe("an external model definition and the entry it names", () => {
    const COMP = "./models/omex_comp.xml";
    const MINIMAL = "./models/omex_minimal.xml";
    const archive = ReportIndex.forEntries(loadFixture("comp_models").reports);
    const comp = archive.get(COMP)!;
    const minimal = archive.get(MINIMAL)!;
    const replaced = [...comp.elements.values()].find((e) => e.metaId === "S0_RE")!;

    it("links the element of the other entry and names its document", async () => {
      await router.push("/examples/CompModels?q=S0&types=Species");
      const wrapper = mountWith(LinksColumn, { pk: replaced.pk }, comp);
      const links = wrapper
        .get("[data-testid=links-references]")
        .findAll("[data-testid=element-link]");
      const across = links.filter((link) => link.attributes("data-entry") === MINIMAL);
      expect(across).toHaveLength(1);
      expect(across[0]!.attributes("data-pk")).toBe("omex_minimal/Species:S1");
      expect(across[0]!.get("[data-testid=element-link-entry]").text()).toBe("omex_minimal.xml");
      // the link opens the other entry on the model of the element, without the search and
      // the type filter of this one
      const href = new URL(across[0]!.attributes("href")!, "http://localhost");
      expect(Object.fromEntries(href.searchParams)).toEqual({
        entry: MINIMAL,
        model: "omex_minimal",
        pk: "omex_minimal/Species:S1",
      });
      // the submodel is an element of the entry which is shown, and names no document
      const local = links.filter((link) => !link.attributes("data-entry"));
      expect(local.map((link) => link.attributes("data-pk"))).toEqual([
        "omex_comp/Submodel:submodel0",
      ]);
      expect(local[0]!.find("[data-testid=element-link-entry]").exists()).toBe(false);
    });

    it("lists who names an element from another entry", () => {
      const wrapper = mountWith(LinksColumn, { pk: "omex_minimal/Species:S1" }, minimal);
      const group = wrapper
        .get("[data-testid=links-referenced-by]")
        .get("[data-testid=links-replacedElement]");
      const links = group.findAll("[data-testid=element-link]");
      expect(links).toHaveLength(5);
      for (const link of links) expect(link.attributes("data-entry")).toBe(COMP);
      // a replacement is named after the element it belongs to and its submodel, in its entry
      expect(links[0]!.text()).toContain("S0.submodel0");
      expect(links[0]!.text()).toContain("omex_comp.xml");
    });

    it("shows the replaced element of the other entry in the attributes", () => {
      const wrapper = mountWith(ReplacedElementAttributes, { element: replaced }, comp);
      const link = wrapper
        .findAll("[data-testid=element-link]")
        .find((l) => l.attributes("data-entry") === MINIMAL);
      expect(link?.text()).toContain("S1_port");
    });

    it("shows how far the definition was followed", () => {
      const emd = comp.externalModelDefinitions[0]!;
      const wrapper = mountWith(ExternalModelDefinitionAttributes, { element: emd }, comp);
      expect(wrapper.get("[data-testid=resolution-status]").text()).toBe("resolved");
      expect(wrapper.get("[data-testid=resolution-entry]").text()).toBe(MINIMAL);
      const model = wrapper.get("[data-testid=resolution-model]");
      expect(model.attributes("data-pk")).toBe("omex_minimal/Model:omex_minimal");
      expect(model.attributes("data-entry")).toBe(MINIMAL);
      expect(wrapper.find("[data-testid=resolution-md5]").exists()).toBe(false);
    });

    it("states the result of the md5 check", () => {
      const deletion = ReportIndex.forEntries(loadFixture("comp_deletion").reports).get(
        "./comp_deletion.xml",
      )!;
      const emd = deletion.externalModelDefinitions[0]!;
      const wrapper = mountWith(ExternalModelDefinitionAttributes, { element: emd }, deletion);
      expect(wrapper.get("[data-testid=resolution-md5]").text()).toBe("matches the document");
      const changed = { ...emd, resolution: { ...emd.resolution, md5Matches: false } };
      const mismatch = mountWith(ExternalModelDefinitionAttributes, { element: changed }, deletion);
      expect(mismatch.get("[data-testid=resolution-md5]").text()).toBe(
        "does not match the document",
      );
    });

    it("says why a definition is not followed, at the definition and at its submodel", () => {
      // the report of an upload of the file alone: no other entry, nothing resolved
      const report = structuredClone(loadReport("comp_models", COMP));
      for (const emd of report.externalModelDefinitions ?? []) {
        emd.resolution = { status: "notFound", entry: null, model: null, md5Matches: null };
      }
      report.linkGraph!.edges = report.linkGraph!.edges!.filter((edge) => !edge.targetEntry);
      const alone = new ReportIndex(report, "./model.xml");
      const emd = alone.externalModelDefinitions[0]!;
      const wrapper = mountWith(ExternalModelDefinitionAttributes, { element: emd }, alone);
      const status = wrapper.get("[data-testid=resolution-status]");
      expect(status.text()).toBe("no document at the source");
      expect(status.attributes("data-status")).toBe("notFound");
      expect(wrapper.find("[data-testid=resolution-model]").exists()).toBe(false);

      const submodel = alone.mainModel!.listOfSubmodels![0]!;
      const submodelWrapper = mountWith(SubmodelAttributes, { element: submodel }, alone);
      expect(submodelWrapper.get("[data-testid=resolution-status]").text()).toBe(
        "no document at the source",
      );
    });

    it("links the external model at a submodel which instantiates it", () => {
      const submodel = comp.mainModel!.listOfSubmodels![0]!;
      const wrapper = mountWith(SubmodelAttributes, { element: submodel }, comp);
      const link = wrapper
        .findAll("[data-testid=element-link]")
        .find((l) => l.attributes("data-entry") === MINIMAL);
      expect(link?.attributes("data-pk")).toBe("omex_minimal/Model:omex_minimal");
    });
  });
});
