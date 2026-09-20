import type { ElementType } from "@/api/types";
import { ID_COLUMNS, type ColumnSpec } from "@/report/columns/types";

type PackageType = Extract<
  ElementType,
  | "Submodel"
  | "Port"
  | "GeneProduct"
  | "Objective"
  | "FluxBound"
  | "UserDefinedConstraint"
  | "QualitativeSpecies"
  | "Transition"
>;

export const PACKAGE_COLUMNS: Readonly<Record<PackageType, readonly ColumnSpec[]>> = {
  Submodel: [
    ...ID_COLUMNS,
    { field: "modelRef", kind: "link", link: "modelRef" },
    {
      field: "timeConversionFactor",
      kind: "link",
      link: "timeConversionFactor",
    },
    {
      field: "extentConversionFactor",
      kind: "link",
      link: "extentConversionFactor",
    },
    { field: "listOfDeletions", kind: "elements" },
  ],
  Port: [
    ...ID_COLUMNS,
    { field: "portRef", kind: "text" },
    { field: "idRef", kind: "link", link: "port" },
    { field: "unitRef", kind: "link", link: "port" },
    { field: "metaIdRef", kind: "link", link: "port" },
  ],
  GeneProduct: [
    ...ID_COLUMNS,
    { field: "label", kind: "text" },
    {
      field: "associatedSpecies",
      kind: "link",
      link: "associatedSpecies",
    },
  ],
  Objective: [
    ...ID_COLUMNS,
    { field: "type", kind: "text" },
    // the terms of the objective as the sum they are, which is what the objective optimises
    { field: "listOfFluxObjectives", kind: "terms" },
  ],
  FluxBound: [
    ...ID_COLUMNS,
    { field: "reaction", kind: "link", link: "fluxBound" },
    { field: "operation", kind: "text" },
    { field: "value", kind: "number" },
  ],
  UserDefinedConstraint: [
    ...ID_COLUMNS,
    { field: "lowerBound", kind: "link", link: "lowerBound" },
    { field: "upperBound", kind: "link", link: "upperBound" },
    // the weighted sum the two bounds keep between them
    { field: "listOfUserDefinedConstraintComponents", kind: "terms" },
  ],
  QualitativeSpecies: [
    ...ID_COLUMNS,
    { field: "compartment", kind: "link", link: "compartment" },
    { field: "initialLevel", kind: "number" },
    { field: "maxLevel", kind: "number" },
    { field: "constant", kind: "boolean" },
  ],
  // the species of the inputs with their sign and the species of the outputs are the influence
  // the transition encodes, which is what a reader of a qualitative model looks for first, and
  // the function terms with their math are the rule which decides it
  Transition: [
    ...ID_COLUMNS,
    { field: "listOfInputs", kind: "influence", link: "input" },
    { field: "listOfOutputs", kind: "influence", link: "output" },
    { field: "listOfFunctionTerms", kind: "functionTerms" },
  ],
};
