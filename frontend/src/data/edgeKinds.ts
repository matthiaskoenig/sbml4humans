import type { EdgeKind } from "@/api/types";

/** The fixed order of the link groups in the inspector. */
export const EDGE_KINDS: readonly EdgeKind[] = [
  "compartment",
  "reactant",
  "product",
  "modifier",
  "trigger",
  "priority",
  "delay",
  "variable",
  "symbol",
  "units",
  "conversionFactor",
  "fluxBound",
  "geneProduct",
  "associatedSpecies",
  "fluxObjective",
  "modelRef",
  "port",
  "deletion",
  "replacedBy",
  "replacedElement",
  "math",
];

const LABELS: Readonly<Record<EdgeKind, string>> = {
  compartment: "compartment",
  reactant: "reactant",
  product: "product",
  modifier: "modifier",
  trigger: "trigger",
  priority: "priority",
  delay: "delay",
  variable: "variable",
  symbol: "symbol",
  units: "units",
  conversionFactor: "conversion factor",
  fluxBound: "flux bound",
  geneProduct: "gene product",
  associatedSpecies: "associated species",
  fluxObjective: "flux objective",
  modelRef: "model reference",
  port: "port",
  deletion: "deletion",
  replacedBy: "replaced by",
  replacedElement: "replaced element",
  math: "math",
};

export function edgeKindLabel(kind: EdgeKind): string {
  return LABELS[kind];
}
