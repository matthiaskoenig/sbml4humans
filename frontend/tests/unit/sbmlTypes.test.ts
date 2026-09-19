import { describe, expect, it } from "vitest";

import { EDGE_KINDS, edgeKindLabel } from "@/data/edgeKinds";
import {
  DOCUMENT_TYPES,
  ELEMENT_TYPES,
  NESTED_TYPES,
  SBML_TYPES,
  isElementType,
  typeInfo,
} from "@/data/sbmlTypes";

describe("sbml types", () => {
  it("lists the element types in specification order, the unit definitions last", () => {
    expect(ELEMENT_TYPES.map((t) => t.type)).toEqual([
      "FunctionDefinition",
      "Compartment",
      "Species",
      "Parameter",
      "InitialAssignment",
      "AssignmentRule",
      "RateRule",
      "AlgebraicRule",
      "Constraint",
      "Reaction",
      "Event",
      "Submodel",
      "Port",
      "GeneProduct",
      "Objective",
      "FluxBound",
      "UserDefinedConstraint",
      "QualitativeSpecies",
      "Transition",
      "UnitDefinition",
    ]);
  });

  it("knows every type once", () => {
    const all = [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES];
    expect(new Set(all.map((t) => t.type)).size).toBe(all.length);
    expect(Object.keys(SBML_TYPES)).toHaveLength(all.length);
    for (const info of all) {
      expect(typeInfo(info.type)).toBe(info);
      expect(info.color).toMatch(/^#[0-9a-f]{6}$/);
      expect(info.icon, info.type).toBeDefined();
      // a type has no name besides the name of its class, neither a label nor a plural
      expect(info, info.type).not.toHaveProperty("label");
      expect(info, info.type).not.toHaveProperty("plural");
    }
  });

  it("marks the package of the qual types", () => {
    expect(typeInfo("QualitativeSpecies").pkg).toBe("qual");
    expect(typeInfo("Transition").pkg).toBe("qual");
    expect(typeInfo("Input").pkg).toBe("qual");
    expect(typeInfo("Output").pkg).toBe("qual");
    expect(typeInfo("FunctionTerm").pkg).toBe("qual");
    expect(typeInfo("DefaultTerm").pkg).toBe("qual");
  });

  it("marks the package of the distrib types", () => {
    expect(typeInfo("Uncertainty").pkg).toBe("distrib");
    expect(typeInfo("UncertParameter").pkg).toBe("distrib");
    expect(typeInfo("UncertSpan").pkg).toBe("distrib");
    expect(typeInfo("UncertSpan").type).toBe("UncertSpan");
  });

  it("marks the package of the comp and fbc types", () => {
    expect(typeInfo("Submodel").pkg).toBe("comp");
    expect(typeInfo("Port").pkg).toBe("comp");
    expect(typeInfo("GeneProduct").pkg).toBe("fbc");
    expect(typeInfo("GeneProductAssociation").pkg).toBe("fbc");
    expect(typeInfo("And").pkg).toBe("fbc");
    expect(typeInfo("Or").pkg).toBe("fbc");
    expect(typeInfo("GeneProductRef").pkg).toBe("fbc");
    expect(typeInfo("Objective").pkg).toBe("fbc");
    expect(typeInfo("FluxObjective").pkg).toBe("fbc");
    expect(typeInfo("FluxBound").pkg).toBe("fbc");
    expect(typeInfo("UserDefinedConstraint").pkg).toBe("fbc");
    expect(typeInfo("UserDefinedConstraintComponent").pkg).toBe("fbc");
    expect(typeInfo("Species").pkg).toBe("core");
  });

  it("maps every element type to its model list", () => {
    for (const info of ELEMENT_TYPES) {
      expect(info.listKey).toMatch(/^listOf/);
    }
    expect(typeInfo("RateRule").listKey).toBe("listOfRules");
    expect(isElementType("Species")).toBe(true);
    expect(isElementType("SBMLDocument")).toBe(false);
  });

  it("orders and labels the edge kinds", () => {
    expect(EDGE_KINDS[0]).toBe("compartment");
    expect(EDGE_KINDS).toHaveLength(48);
    // a reaction names its kinetic law behind its participants, an event its assignments behind
    // its trigger, its priority and its delay
    expect(EDGE_KINDS.indexOf("kineticLaw")).toBe(EDGE_KINDS.indexOf("modifier") + 1);
    expect(EDGE_KINDS.indexOf("localParameter")).toBe(EDGE_KINDS.indexOf("kineticLaw") + 1);
    expect(EDGE_KINDS.indexOf("eventAssignment")).toBe(EDGE_KINDS.indexOf("delay") + 1);
    // an element names its uncertainties and each of them its measures
    expect(EDGE_KINDS.indexOf("uncertainty")).toBe(EDGE_KINDS.indexOf("uncertParameter") - 1);
    expect(edgeKindLabel("kineticLaw")).toBe("kineticLaw");
    expect(edgeKindLabel("eventAssignment")).toBe("eventAssignment");
    expect(edgeKindLabel("geneProductAssociation")).toBe("geneProductAssociation");
    expect(edgeKindLabel("fluxBound")).toBe("fluxBound");
    expect(edgeKindLabel("replacedBy")).toBe("replacedBy");
    expect(edgeKindLabel("localParameter")).toBe("localParameter");
    expect(edgeKindLabel("externalModelDefinition")).toBe("externalModelDefinition");
    expect(edgeKindLabel("sBaseRef")).toBe("sBaseRef");
    expect(edgeKindLabel("functionTerm")).toBe("functionTerm");
    expect(edgeKindLabel("defaultTerm")).toBe("defaultTerm");
    expect(edgeKindLabel("uncertainty")).toBe("uncertainty");
    expect(edgeKindLabel("uncertParameter")).toBe("uncertParameter");
    expect(edgeKindLabel("var")).toBe("var");
    // an attribute of a pair has a kind of its own, so the element it names says which it is
    expect(EDGE_KINDS.indexOf("varUpper")).toBe(EDGE_KINDS.indexOf("varLower") + 1);
    expect(edgeKindLabel("lowerFluxBound")).toBe("lowerFluxBound");
    expect(edgeKindLabel("reaction2")).toBe("reaction2");
    expect(edgeKindLabel("variable2")).toBe("variable2");
    expect(edgeKindLabel("timeConversionFactor")).toBe("timeConversionFactor");
    // a link group is named by the key of its kind, the name of the attribute which makes the
    // reference, and by no words of its own
    for (const kind of EDGE_KINDS) expect(edgeKindLabel(kind), kind).toBe(kind);
  });
});
