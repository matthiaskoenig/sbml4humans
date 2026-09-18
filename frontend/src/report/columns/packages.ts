import type { ElementType } from "@/api/types";
import { ID_COLUMNS, type ColumnDef } from "@/report/columns/types";

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

export const PACKAGE_COLUMNS: Readonly<Record<PackageType, readonly ColumnDef[]>> = {
  Submodel: [
    ...ID_COLUMNS,
    { field: "modelRef", header: "model", kind: "link", link: "modelRef" },
    {
      field: "timeConversionFactor",
      header: "time conversion factor",
      kind: "link",
      link: "conversionFactor",
    },
    {
      field: "extentConversionFactor",
      header: "extent conversion factor",
      kind: "link",
      link: "conversionFactor",
    },
    { field: "listOfDeletions.length", header: "deletions", kind: "count" },
  ],
  Port: [
    ...ID_COLUMNS,
    { field: "portRef", header: "port ref", kind: "text" },
    { field: "idRef", header: "id ref", kind: "link", link: "port" },
    { field: "unitRef", header: "unit ref", kind: "link", link: "port" },
    { field: "metaIdRef", header: "meta id ref", kind: "link", link: "port" },
  ],
  GeneProduct: [
    ...ID_COLUMNS,
    { field: "label", header: "label", kind: "text" },
    {
      field: "associatedSpecies",
      header: "associated species",
      kind: "link",
      link: "associatedSpecies",
    },
  ],
  Objective: [
    ...ID_COLUMNS,
    { field: "type", header: "type", kind: "text" },
    { field: "listOfFluxObjectives.length", header: "flux objectives", kind: "count" },
  ],
  FluxBound: [
    ...ID_COLUMNS,
    { field: "reaction", header: "reaction", kind: "link", link: "fluxBound" },
    { field: "operation", header: "operation", kind: "text" },
    { field: "value", header: "value", kind: "number" },
  ],
  UserDefinedConstraint: [
    ...ID_COLUMNS,
    { field: "lowerBound", header: "lower bound", kind: "link", link: "fluxBound" },
    { field: "upperBound", header: "upper bound", kind: "link", link: "fluxBound" },
    {
      field: "listOfUserDefinedConstraintComponents.length",
      header: "components",
      kind: "count",
    },
  ],
  QualitativeSpecies: [
    ...ID_COLUMNS,
    { field: "compartment", header: "compartment", kind: "link", link: "compartment" },
    { field: "initialLevel", header: "initial level", kind: "number" },
    { field: "maxLevel", header: "max level", kind: "number" },
    { field: "constant", header: "constant", kind: "boolean" },
  ],
  // the species of the inputs with their sign and the species of the outputs are the influence
  // the transition encodes, which is what a reader of a qualitative model looks for first
  Transition: [
    ...ID_COLUMNS,
    { field: "listOfInputs", header: "inputs", kind: "influence", link: "input" },
    { field: "listOfOutputs", header: "outputs", kind: "influence", link: "output" },
    { field: "listOfFunctionTerms.length", header: "function terms", kind: "count" },
  ],
};
