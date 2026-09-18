import { describe, expect, it } from "vitest";

import type { Reaction, Species } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { elementLabel } from "@/report/label";

import { loadFixture, loadReport, type FixtureName } from "./fixtures";

const repressilator = new ReportIndex(loadReport("repressilator"));
const icgBody = new ReportIndex(loadReport("icg_body"));
const definitions = new ReportIndex(loadReport("model_definitions"));
const distrib = new ReportIndex(loadReport("distrib_uncertainties"));
const compDeletion = new ReportIndex(loadReport("comp_deletion"));

const FIXTURE_NAMES: FixtureName[] = [
  "repressilator",
  "icg_body",
  "fbc_example",
  "model_definitions",
  "comp_models",
  "comp_deletion",
  "distrib_uncertainties",
];

/** Every report entry of every fixture, indexed - `comp_models` alone carries three entries. */
function allReportIndexes(): ReportIndex[] {
  return FIXTURE_NAMES.flatMap((name) =>
    Object.values(loadFixture(name).reports).map((entry) => new ReportIndex(entry.report)),
  );
}

describe("ReportIndex", () => {
  it("indexes the document, the models and every element by pk", () => {
    expect(repressilator.get(repressilator.document.pk)?.sbmlType).toBe("SBMLDocument");
    const model = repressilator.mainModel;
    expect(model?.id).toBe("BIOMD0000000012");
    expect(repressilator.get(model!.pk)).toBe(model);
    for (const species of model!.listOfSpecies!) {
      expect(repressilator.get(species.pk)).toBe(species);
    }
  });

  it("indexes the nested elements", () => {
    const reaction = repressilator.mainModel!.listOfReactions!.find(
      (r) => r.listOfReactants!.length > 0 && r.kineticLaw,
    )!;
    const reactant = reaction.listOfReactants![0]!;
    expect(repressilator.get(reactant.pk)).toBe(reactant);
    expect(repressilator.get(reaction.kineticLaw!.pk)).toBe(reaction.kineticLaw);
    for (const parameter of reaction.kineticLaw!.listOfLocalParameters!) {
      expect(repressilator.get(parameter.pk)).toBe(parameter);
    }
    const uncertainty = [...distrib.elements.values()].find((e) => e.sbmlType === "Uncertainty");
    expect(uncertainty).toBeDefined();
  });

  it("indexes the external model definitions", () => {
    expect(icgBody.externalModelDefinitions).toHaveLength(1);
    const emd = icgBody.externalModelDefinitions[0]!;
    expect(icgBody.get(emd.pk)).toBe(emd);
  });

  it("groups the elements of a model by type in list order", () => {
    const byType = repressilator.byType("BIOMD0000000012");
    expect([...byType.keys()]).toHaveLength(20);
    expect(byType.get("Species")).toEqual(repressilator.mainModel!.listOfSpecies);
    expect(byType.get("Submodel")).toEqual([]);
    const rules = definitions.byType("model_definitions");
    expect(rules.get("AssignmentRule")!.every((r) => r.sbmlType === "AssignmentRule")).toBe(true);
  });

  it("knows the main model and the model definitions", () => {
    expect(definitions.models.map((m) => m.kind)).toEqual(["model", "modelDefinition"]);
    expect(definitions.mainModel?.id).toBe("model_definitions");
    expect(definitions.model("m1")?.kind).toBe("modelDefinition");
    expect(definitions.model("nope")).toBeNull();
  });

  it("indexes the edges in both directions", () => {
    const species = repressilator.mainModel!.listOfSpecies![0]!;
    const compartmentEdge = repressilator
      .references(species.pk)
      .find((e) => e.kind === "compartment");
    expect(compartmentEdge).toBeDefined();
    const compartment = repressilator.get(compartmentEdge!.target)!;
    expect(compartment.sbmlType).toBe("Compartment");
    expect(repressilator.referencedBy(compartment.pk)).toContainEqual(compartmentEdge);
    expect(repressilator.referencedBy("nope")).toEqual([]);
  });

  it("resolves a reference by edge kind and id", () => {
    const species = repressilator.mainModel!.listOfSpecies![0] as Species;
    const pk = repressilator.resolve(species.pk, "compartment", species.compartment);
    expect(pk).not.toBeNull();
    expect(repressilator.get(pk!)?.id).toBe(species.compartment);
    expect(repressilator.resolve(species.pk, "compartment", "nope")).toBeNull();
    expect(repressilator.resolve(species.pk, "units", "litre")).toBeNull();
  });

  it("resolves a port reference by metaId, not only by id", () => {
    // no fixture port sets metaIdRef (all are id references), so this exercises only the miss:
    // an unknown metaId does not resolve, through the id path or the metaId fallback.
    const port = icgBody.mainModel!.listOfPorts!.find((p) => p.idRef)!;
    expect(icgBody.resolve(port.pk, "port", "unknown-meta-id")).toBeNull();
  });

  it("resolves the species of a reactant from the species reference", () => {
    // the reaction links to its reactant, the reactant links to its species, both as "reactant"
    const reaction = repressilator.mainModel!.listOfReactions!.find(
      (r) => r.listOfReactants!.length > 0,
    ) as Reaction;
    const reactant = reaction.listOfReactants![0]!;
    const pk = repressilator.resolve(reactant.pk, "reactant", reactant.species);
    expect(repressilator.get(pk!)?.sbmlType).toBe("Species");
    expect(repressilator.resolve(reaction.pk, "reactant", reactant.species)).toBeNull();
  });

  it("tells the reaction of a species reference and the role it plays in it", () => {
    const model = repressilator.mainModel!;
    const reaction = model.listOfReactions!.find((r) => r.listOfModifiers!.length > 0) as Reaction;
    const modifier = reaction.listOfModifiers![0]!;
    expect(repressilator.participation(modifier.pk)).toEqual({
      reaction: reaction.pk,
      role: "modifier",
    });
    const reactant = model.listOfReactions!.find((r) => r.listOfReactants!.length > 0)!
      .listOfReactants![0]!;
    expect(repressilator.participation(reactant.pk)?.role).toBe("reactant");
    // a species is no participation, it is what one names
    expect(repressilator.participation(model.listOfSpecies![0]!.pk)).toBeNull();
  });

  it("tells the model of an element", () => {
    const species = repressilator.mainModel!.listOfSpecies![0]!;
    expect(repressilator.modelOf(species.pk)).toBe("BIOMD0000000012");
    expect(repressilator.modelOf("nope")).toBeNull();

    // a nested element (a species reference) resolves to the same model id as its reaction
    const reaction = repressilator.mainModel!.listOfReactions!.find(
      (r) => r.listOfReactants!.length > 0,
    )!;
    const reactant = reaction.listOfReactants![0]!;
    expect(repressilator.modelOf(reactant.pk)).toBe("BIOMD0000000012");

    // an element of a model definition resolves to the model definition's id, not the main model's
    const m1Species = definitions.model("m1")!.listOfSpecies![0];
    if (m1Species) expect(definitions.modelOf(m1Species.pk)).toBe("m1");
  });

  it("keys every species and modifier reference pk uniquely within its report", () => {
    // the backend derives a nested reference's pk from its parent reaction, not a digest of its
    // own content, so that the edge of the reaction reaches exactly one reference.
    let checked = 0;
    for (const index of allReportIndexes()) {
      const pks: string[] = [];
      for (const model of index.models) {
        const reactions = (index.byType(model.id ?? "").get("Reaction") ?? []) as Reaction[];
        for (const reaction of reactions) {
          for (const reference of [
            ...(reaction.listOfReactants ?? []),
            ...(reaction.listOfProducts ?? []),
            ...(reaction.listOfModifiers ?? []),
          ]) {
            pks.push(reference.pk);
          }
        }
      }
      expect(new Set(pks).size).toBe(pks.length);
      checked += pks.length;
    }
    expect(checked).toBeGreaterThan(50);
  });

  it("indexes the replacements, the deletions and the reference chains of comp", () => {
    // the replacements and the deletions carry a pk of their own, so the inspector opens them
    // like any other element and a link reaches them
    const species = compDeletion.mainModel!.listOfSpecies![0]!;
    const replaced = species.comp!.replacedElements![0]!;
    expect(compDeletion.get(replaced.pk)).toBe(replaced);
    const submodel = compDeletion.mainModel!.listOfSubmodels![0]!;
    const deletion = submodel.listOfDeletions![0]!;
    expect(compDeletion.get(deletion.pk)).toBe(deletion);
    const compartment = compDeletion.mainModel!.listOfCompartments![0]!;
    const nested = compartment.comp!.replacedElements!.find((r) => r.sbaseRef)!.sbaseRef!;
    expect(compDeletion.get(nested.pk)).toBe(nested);
    const parameter = compDeletion.mainModel!.listOfParameters!.find((p) => p.comp?.replacedBy)!
      .comp!.replacedBy!;
    expect(compDeletion.get(parameter.pk)).toBe(parameter);
  });

  it("names a replacement after its element and the submodel it reaches into", () => {
    const species = compDeletion.mainModel!.listOfSpecies![0]!;
    const replaced = species.comp!.replacedElements![0]!;
    expect(elementLabel(compDeletion, replaced.pk)).toBe(`${species.id}.${replaced.submodelRef}`);
  });
});
