import { describe, expect, it } from "vitest";

import type { Edge, Reaction, SBase, Species } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { elementLabel } from "@/report/label";

import { loadFixture, loadReport, type FixtureName } from "./fixtures";

const repressilator = new ReportIndex(loadReport("repressilator"));
const icgBody = new ReportIndex(loadReport("icg_body"));
const definitions = new ReportIndex(loadReport("model_definitions"));
const distrib = new ReportIndex(loadReport("distrib_uncertainties"));
const compDeletion = new ReportIndex(loadReport("comp_deletion"));
const fbcConstraints = new ReportIndex(loadReport("fbc_constraints_v3"));
const fbcBounds = new ReportIndex(loadReport("fbc_bounds_v1"));

const FIXTURE_NAMES: FixtureName[] = [
  "repressilator",
  "icg_body",
  "fbc_example",
  "model_definitions",
  "comp_models",
  "comp_deletion",
  "distrib_uncertainties",
  "qual_example",
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

  // the inputs, the outputs and the terms of a transition were nodes of the graph before they
  // were elements of the index, so the identifier of an input in the inspector of its
  // transition was written as text instead of the link to that input
  it("indexes every node of the link graph of every fixture", () => {
    for (const index of allReportIndexes()) {
      const missing = [...index.nodes.keys()].filter((pk) => !index.has(pk));
      expect(missing).toEqual([]);
    }
  });

  it("indexes the inputs, the outputs and the terms of a transition", () => {
    const qual = new ReportIndex(loadReport("qual_example"));
    const transition = qual.mainModel!.listOfTransitions![0]!;
    expect(qual.get(transition.listOfInputs![0]!.pk)).toBe(transition.listOfInputs![0]);
    expect(qual.get(transition.listOfOutputs![0]!.pk)).toBe(transition.listOfOutputs![0]);
    expect(qual.get(transition.listOfFunctionTerms![0]!.pk)).toBe(
      transition.listOfFunctionTerms![0],
    );
    expect(qual.get(transition.defaultTerm!.pk)).toBe(transition.defaultTerm);
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

  it("names a kinetic law and an event assignment after the element they belong to", () => {
    // the curated models key both by their meta id, which says nothing about where they belong
    const reaction = repressilator.mainModel!.listOfReactions!.find((r) => r.id === "Reaction7")!;
    expect(reaction.kineticLaw!.id).toBeNull();
    expect(elementLabel(repressilator, reaction.kineticLaw!.pk)).toBe("Reaction7.kineticLaw");

    const cellCycle = new ReportIndex(loadReport("cell_cycle"));
    const division = cellCycle.mainModel!.listOfEvents!.find((e) => e.id === "Division")!;
    const labels = division.listOfEventAssignments!.map((a) => elementLabel(cellCycle, a.pk));
    expect(labels).toEqual(["Division.kp", "Division.Mass"]);

    // an element which carries an id of its own is named by it
    const constraintEvent = new ReportIndex(loadReport("constraint_event"));
    const assignment = constraintEvent.mainModel!.listOfEvents![0]!.listOfEventAssignments![0]!;
    expect(elementLabel(constraintEvent, assignment.pk)).toBe(assignment.id);
  });

  it("names a nested element after the name its owner has, whatever keys the two", () => {
    // an event may carry no id, and a term of a transition a meta id: the trigger is named after
    // the name of its event, the term after its transition and its place in the table
    const event = { pk: "m/Event:metaid_1", sbmlType: "Event", id: null };
    const trigger = { pk: "m/Trigger:_2", sbmlType: "Trigger", id: null };
    const term = { pk: "m/FunctionTerm:meta_term", sbmlType: "FunctionTerm", id: null };
    const transition = {
      pk: "m/Transition:tr",
      sbmlType: "Transition",
      id: "tr",
      listOfFunctionTerms: [{ pk: "m/FunctionTerm:tr.functionTerm.0" }, term],
    };
    const elements = new Map<string, unknown>(
      [event, trigger, term, transition].map((element) => [element.pk, element]),
    );
    const edges: Edge[] = [
      { source: event.pk, target: trigger.pk, kind: "trigger" },
      { source: transition.pk, target: term.pk, kind: "functionTerm" },
    ];
    const fake = {
      get: (pk: string) => elements.get(pk) as SBase | undefined,
      referencedBy: (pk: string) => edges.filter((edge) => edge.target === pk),
    } as unknown as ReportIndex;
    expect(elementLabel(fake, trigger.pk)).toBe("metaid_1.trigger");
    expect(elementLabel(fake, term.pk)).toBe("tr.functionTerm.1");
  });

  it("tells the reaction a node of a gene product association belongs to, and its genes", () => {
    const model = fbcConstraints.mainModel!;
    const v1 = model.listOfReactions!.find((r) => r.id === "v1")!;
    const or = v1.fbc!.geneProductAssociation!.association!;
    const and = or.sbmlType === "Or" ? or.associations![0]! : null;
    const leaf = and?.sbmlType === "And" ? and.associations![0]! : null;
    for (const node of [v1.fbc!.geneProductAssociation!, or, and!, leaf!]) {
      expect(fbcConstraints.associationReaction(node.pk)).toBe(v1.pk);
    }
    expect(fbcConstraints.associationReaction(v1.pk)).toBeNull();
    expect(fbcConstraints.geneProducts(v1.pk)).toEqual([
      "fbc_constraints_v3/GeneProduct:g_ptsG",
      "fbc_constraints_v3/GeneProduct:g_ptsH",
      "fbc_constraints_v3/GeneProduct:g_galP",
    ]);
    const exchange = model.listOfReactions!.find((r) => r.id === "EX_glc")!;
    expect(fbcConstraints.geneProducts(exchange.pk)).toEqual([]);
  });

  it("names a gene product reference after its reaction and its gene", () => {
    // a reference without an id named by its gene alone read as the gene product itself, so
    // the gene product listed its own id once for every reaction which needs it
    const v2 = fbcConstraints.mainModel!.listOfReactions!.find((r) => r.id === "v2")!;
    const leaf = v2.fbc!.geneProductAssociation!.association!;
    expect(leaf.sbmlType).toBe("GeneProductRef");
    expect(elementLabel(fbcConstraints, leaf.pk)).toBe("v2.g_galP");
    // a reference with an id keeps it
    expect(elementLabel(fbcConstraints, "fbc_constraints_v3/GeneProductRef:ref_galP")).toBe(
      "ref_galP",
    );
  });

  it("names a flux objective after its objective and the reactions it multiplies", () => {
    // named by its reaction alone, a flux objective read as the reaction it weighs
    const objective = fbcBounds.mainModel!.listOfObjectives!.find((o) => o.id === "biomass_max")!;
    const term = objective.listOfFluxObjectives![0]!;
    expect(term.id ?? null).toBeNull();
    expect(elementLabel(fbcBounds, term.pk)).toBe("biomass_max.EX_biomass");
    const fake = {
      get: (pk: string) =>
        pk === "m/FluxObjective:q"
          ? { pk, sbmlType: "FluxObjective", reaction: "R1", reaction2: "R2" }
          : { pk, sbmlType: "Objective", id: "obj" },
      referencedBy: (pk: string) =>
        pk === "m/FluxObjective:q"
          ? [{ source: "m/Objective:obj", target: pk, kind: "fluxObjective" }]
          : [],
    } as unknown as ReportIndex;
    expect(elementLabel(fake, "m/FluxObjective:q")).toBe("obj.R1.R2");
  });

  it("names an external parameter without an id by the last segment of its definition", () => {
    // its key carries the whole url, which a link would spell out
    const pk =
      "m/UncertParameter:u.externalParameter.https://en.wikipedia.org/wiki/Beta_distribution#alpha";
    const fake = {
      get: (key: string) =>
        key === pk
          ? {
              pk,
              sbmlType: "UncertParameter",
              type: "externalParameter",
              definitionUrl: "https://en.wikipedia.org/wiki/Beta_distribution#alpha",
            }
          : { pk: key, sbmlType: "Uncertainty", id: "u_Vmax" },
      referencedBy: (key: string) =>
        key === pk ? [{ source: "m/Uncertainty:u", target: pk, kind: "uncertParameter" }] : [],
    } as unknown as ReportIndex;
    expect(elementLabel(fake, pk)).toBe("u_Vmax.alpha");
  });

  it("names a replacement after its element and the submodel it reaches into", () => {
    const species = compDeletion.mainModel!.listOfSpecies![0]!;
    const replaced = species.comp!.replacedElements![0]!;
    expect(elementLabel(compDeletion, replaced.pk)).toBe(`${species.id}.${replaced.submodelRef}`);
  });

  describe("the entries of an archive", () => {
    const COMP = "./models/omex_comp.xml";
    const MINIMAL = "./models/omex_minimal.xml";
    const indexes = ReportIndex.forEntries(loadFixture("comp_models").reports);
    const comp = indexes.get(COMP)!;
    const minimal = indexes.get(MINIMAL)!;
    const replaced = [...comp.elements.values()].find(
      (element) => element.sbmlType === "ReplacedElement" && element.metaId === "S0_RE",
    )!;

    it("knows its location and the other entries", () => {
      expect(comp.location).toBe(COMP);
      expect(comp.entry(null)).toBe(comp);
      expect(comp.entry(COMP)).toBe(comp);
      expect(comp.entry(MINIMAL)).toBe(minimal);
      expect(comp.entry("./missing.xml")).toBeNull();
    });

    it("keeps an edge into another entry apart from the edges of its own", () => {
      expect(comp.referencesAcross(replaced.pk)).toEqual([
        {
          source: replaced.pk,
          sourceEntry: COMP,
          target: "omex_minimal/Species:S1",
          targetEntry: MINIMAL,
          kind: "replacedElement",
        },
      ]);
      // the edge to the submodel stays an edge of the entry, the one across is none of them
      expect(comp.references(replaced.pk).map((edge) => edge.target)).toEqual([
        "omex_comp/Submodel:submodel0",
      ]);
      for (const index of indexes.values()) {
        for (const pk of index.elements.keys()) {
          for (const edge of [...index.references(pk), ...index.referencedBy(pk)]) {
            expect(edge.targetEntry ?? null).toBeNull();
            expect(index.nodes.has(edge.target)).toBe(true);
          }
        }
      }
    });

    it("tells an element who names it from another entry", () => {
      const across = minimal.referencedAcross("omex_minimal/Species:S1");
      expect(across).toHaveLength(5);
      expect(new Set(across.map((edge) => edge.sourceEntry))).toEqual(new Set([COMP]));
      expect(across.map((edge) => edge.source)).toContain(replaced.pk);
      // the model is named by the five external model definitions which instantiate it
      const model = minimal.referencedAcross(minimal.mainModel!.pk);
      expect(model.map((edge) => edge.kind)).toEqual(Array(5).fill("modelRef"));
      expect(minimal.modelIdOf(minimal.mainModel!.pk)).toBe("omex_minimal");
      expect(minimal.modelIdOf("omex_minimal/Species:S1")).toBe("omex_minimal");
    });

    it("drops the edges into another entry from a report on its own", () => {
      const alone = new ReportIndex(loadReport("comp_models", COMP));
      expect(alone.location).toBeNull();
      expect(alone.referencesAcross(replaced.pk)).toEqual([]);
      expect(alone.references(replaced.pk)).toHaveLength(1);
    });
  });
});
