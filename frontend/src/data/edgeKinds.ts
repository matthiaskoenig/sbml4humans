import type { EdgeKind } from "@/api/types";
import { linkEntry } from "@/report/glossary";

/** The fixed order of the link groups in the inspector. */
export const EDGE_KINDS: readonly EdgeKind[] = [
  "compartment",
  "reactant",
  "product",
  "modifier",
  "kineticLaw",
  "localParameter",
  "trigger",
  "priority",
  "delay",
  "eventAssignment",
  "variable",
  "variable2",
  "symbol",
  "units",
  "conversionFactor",
  "timeConversionFactor",
  "extentConversionFactor",
  "fluxBound",
  "lowerFluxBound",
  "upperFluxBound",
  "geneProduct",
  "geneProductAssociation",
  "associatedSpecies",
  "fluxObjective",
  "reaction2",
  "activeObjective",
  "lowerBound",
  "upperBound",
  "constraintComponent",
  "coefficient",
  "input",
  "output",
  "functionTerm",
  "defaultTerm",
  "uncertainty",
  "uncertParameter",
  "var",
  "varLower",
  "varUpper",
  "model",
  "externalModelDefinition",
  "modelRef",
  "port",
  "deletion",
  "replacedBy",
  "replacedElement",
  "sBaseRef",
  "math",
];

/** The name of a link group: the key of the kind, which is the name of the attribute that makes
 * the reference. The glossary labels every kind that way, and its check enforces it. */
export function edgeKindLabel(kind: EdgeKind): string {
  return linkEntry(kind)?.label ?? kind;
}
