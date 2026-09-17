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
  it("lists the element types in specification order", () => {
    expect(ELEMENT_TYPES.map((t) => t.type)).toEqual([
      "FunctionDefinition",
      "UnitDefinition",
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
    }
  });

  it("marks the package of the comp and fbc types", () => {
    expect(typeInfo("Submodel").pkg).toBe("comp");
    expect(typeInfo("Port").pkg).toBe("comp");
    expect(typeInfo("GeneProduct").pkg).toBe("fbc");
    expect(typeInfo("Objective").pkg).toBe("fbc");
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
    expect(EDGE_KINDS).toHaveLength(17);
    expect(edgeKindLabel("fluxBound")).toBe("flux bound");
    expect(edgeKindLabel("replacedBy")).toBe("replaced by");
  });
});
