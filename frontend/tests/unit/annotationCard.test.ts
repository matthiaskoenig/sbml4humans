import { config, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import { vTooltip } from "@/directives/tooltip";
import { router } from "@/router";
import AnnotationCard, { type AnnotationCardState } from "@/components/misc/AnnotationCard.vue";
import type { AnnotationResource } from "@/types/annotation";

const GO: AnnotationResource = {
  resource: "https://identifiers.org/GO:0006096",
  collection: { prefix: "go", name: "Gene Ontology", homepage: "http://geneontology.org/" },
  identifier: "GO:0006096",
  url: "https://www.ebi.ac.uk/QuickGO/GTerm?id=GO:0006096",
  patternMatch: true,
  providers: [
    { name: "QuickGO", url: "https://www.ebi.ac.uk/QuickGO/GTerm?id=GO:0006096", official: true },
    {
      name: "AmiGO 2",
      url: "https://amigo.geneontology.org/amigo/term/GO:0006096",
      official: false,
    },
  ],
  ontology: {
    ontology: "go",
    label: "glycolytic process",
    iri: "http://purl.obolibrary.org/obo/GO_0006096",
    olsUrl: "https://www.ebi.ac.uk/ols4/ontologies/go/classes?iri=x",
    description: "The breakdown of a carbohydrate into pyruvate.",
    synonyms: ["glycolysis", "a", "b", "c", "d", "e", "f"],
    xrefs: [
      { label: "MetaCyc:P341-PWY", url: "https://biocyc.org/x" },
      { label: "Wikipedia:Glycolysis", url: null },
    ],
  },
  chebi: null,
  uniprot: null,
  warnings: [],
  errors: [],
};

// the help labels link through the router and show tooltips
config.global.plugins = [router];
config.global.directives = { tooltip: vTooltip };

function card(info: AnnotationResource | null, state: AnnotationCardState = "resolved") {
  return mount(AnnotationCard, {
    props: {
      resource: info?.resource ?? "https://identifiers.org/GO:0006096",
      qualifier: "BQB_IS",
      info,
      state,
    },
  });
}

describe("AnnotationCard", () => {
  it("shows the head, the term and the providers of an ontology resource", () => {
    const wrapper = card(GO);
    expect(wrapper.get("[data-testid=annotation-qualifier]").text()).toBe("BQB_IS");
    const collection = wrapper.get("[data-testid=annotation-collection]");
    expect(collection.text()).toBe("Gene Ontology");
    expect(collection.attributes("href")).toBe("http://geneontology.org/");
    const identifier = wrapper.get("[data-testid=annotation-identifier]");
    expect(identifier.text()).toBe("GO:0006096");
    expect(identifier.attributes("href")).toBe(GO.url);
    expect(wrapper.get("[data-testid=annotation-ontology]").text()).toBe("GO");
    expect(wrapper.get("[data-testid=annotation-ontology]").attributes("href")).toBe(
      GO.ontology!.olsUrl,
    );
    expect(wrapper.get("[data-testid=annotation-label]").text()).toBe("glycolytic process");
    expect(wrapper.get("[data-testid=annotation-iri]").attributes("href")).toBe(GO.ontology!.iri);
    expect(wrapper.get("[data-testid=annotation-description]").text()).toBe(
      GO.ontology!.description,
    );
    expect(wrapper.findAll("[data-testid=annotation-providers] a").map((a) => a.text())).toEqual([
      "QuickGO",
      "AmiGO 2",
    ]);
    const xrefs = wrapper.get("[data-testid=annotation-xrefs]");
    expect(xrefs.findAll("a").map((a) => a.text())).toEqual(["MetaCyc:P341-PWY"]);
    expect(xrefs.text()).toContain("Wikipedia:Glycolysis");
    expect(wrapper.find("[data-testid=annotation-pattern-warning]").exists()).toBe(false);
  });

  it("shows five synonyms before a show all", async () => {
    const wrapper = card(GO);
    const synonyms = wrapper.get("[data-testid=annotation-synonyms]");
    expect(synonyms.findAll("[data-testid=annotation-synonym]")).toHaveLength(5);
    await synonyms.get("[data-testid=show-all]").trigger("click");
    expect(wrapper.findAll("[data-testid=annotation-synonym]")).toHaveLength(7);
  });

  it("shows markup of the ontology as text", () => {
    const wrapper = card({
      ...GO,
      ontology: {
        ...GO.ontology!,
        label: "H<sub>2</sub>O",
        synonyms: ["<script>x</script>"],
        description: "<b>bold</b>",
      },
    });
    expect(wrapper.get("[data-testid=annotation-label]").text()).toBe("H<sub>2</sub>O");
    expect(wrapper.find("sub").exists()).toBe(false);
    expect(wrapper.find("script").exists()).toBe(false);
    expect(wrapper.get("[data-testid=annotation-description]").text()).toBe("<b>bold</b>");
  });

  it("shows the chemistry of a ChEBI compound and drops a structure which fails to load", async () => {
    const wrapper = card({
      ...GO,
      collection: { prefix: "chebi", name: "ChEBI", homepage: null },
      identifier: "CHEBI:31696",
      chebi: { formula: "C43H47N2O6S2.Na", charge: 0, mass: "774.981", structure: true },
    });
    const chebi = wrapper.get("[data-testid=annotation-chebi]");
    expect(chebi.text()).toContain("C43H47N2O6S2.Na");
    expect(chebi.text()).toContain("774.981");
    const image = wrapper.get("[data-testid=annotation-structure]");
    expect(image.attributes("src")).toContain("/annotation_structure/CHEBI%3A31696");
    await image.trigger("error");
    expect(wrapper.find("[data-testid=annotation-structure]").exists()).toBe(false);
    expect(wrapper.get("[data-testid=annotation-chebi]").text()).toContain("C43H47N2O6S2.Na");
  });

  it("shows the protein of a UniProt resource", () => {
    const wrapper = card({
      ...GO,
      ontology: null,
      collection: { prefix: "uniprot", name: "UniProt Knowledgebase", homepage: null },
      identifier: "P69905",
      uniprot: {
        entry: "HBA_HUMAN",
        name: "Hemoglobin subunit alpha",
        organism: "Homo sapiens",
        genes: ["HBA1", "HBA2"],
        length: 142,
        function: "Oxygen transport.",
      },
    });
    const uniprot = wrapper.get("[data-testid=annotation-uniprot]");
    for (const text of [
      "Hemoglobin subunit alpha",
      "HBA_HUMAN",
      "Homo sapiens",
      "HBA1, HBA2",
      "142",
      "Oxygen transport.",
    ]) {
      expect(uniprot.text()).toContain(text);
    }
  });

  it("warns of a pattern mismatch and of the warnings and errors of the resource", () => {
    const wrapper = card({
      ...GO,
      patternMatch: false,
      warnings: ["Term 'x' is not on OLS."],
      errors: ["OLS down"],
    });
    expect(wrapper.find("[data-testid=annotation-pattern-warning]").exists()).toBe(true);
    expect(wrapper.findAll("[data-testid=annotation-warning]").map((w) => w.text())).toEqual([
      "Term 'x' is not on OLS.",
      "OLS down",
    ]);
  });

  it("shows the resource as a link while it loads, before it is requested and after it failed", () => {
    const resource = "https://identifiers.org/GO:0006096";
    const loading = card(null, "loading");
    expect(loading.find("[data-testid=annotation-loading]").exists()).toBe(true);
    const idle = card(null, "idle");
    expect(idle.find("[data-testid=annotation-loading]").exists()).toBe(false);
    expect(idle.get("[data-testid=annotation-identifier]").attributes("href")).toBe(resource);
    const failed = card(null, "failed");
    expect(failed.find("[data-testid=annotation-loading]").exists()).toBe(false);
    expect(failed.findAll("[data-testid=annotation-warning]")).toHaveLength(1);
  });
});
