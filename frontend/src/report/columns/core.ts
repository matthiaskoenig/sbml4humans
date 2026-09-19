import type { ElementType } from "@/api/types";
import { ID_COLUMNS, type ColumnSpec } from "@/report/columns/types";

const MATH: ColumnSpec = { field: "math", kind: "math" };
const DERIVED_UNITS: ColumnSpec = {
  field: "derivedUnits",
  kind: "units",
  latexField: "derivedUnits",
};

type CoreType = Exclude<
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

export const CORE_COLUMNS: Readonly<Record<CoreType, readonly ColumnSpec[]>> = {
  FunctionDefinition: [...ID_COLUMNS, MATH],
  UnitDefinition: [...ID_COLUMNS, { field: "unitsLatex", kind: "units", latexField: "unitsLatex" }],
  Compartment: [
    ...ID_COLUMNS,
    { field: "spatialDimensions", kind: "number" },
    { field: "size", kind: "number" },
    { field: "units", kind: "link", link: "units", latexField: "unitsLatex" },
    { field: "constant", kind: "boolean" },
    DERIVED_UNITS,
  ],
  Species: [
    ...ID_COLUMNS,
    { field: "compartment", kind: "link", link: "compartment" },
    { field: "fbc.chemicalFormula", kind: "text", optional: true },
    { field: "fbc.charge", kind: "number", optional: true },
    { field: "initialAmount", kind: "number", optional: true },
    {
      field: "initialConcentration",
      kind: "number",
      optional: true,
    },
    {
      field: "substanceUnits",
      kind: "link",
      link: "units",
      latexField: "unitsLatex",
      optional: true,
    },
    { field: "hasOnlySubstanceUnits", kind: "boolean" },
    { field: "boundaryCondition", kind: "boolean" },
    { field: "constant", kind: "boolean" },
    DERIVED_UNITS,
  ],
  Parameter: [
    ...ID_COLUMNS,
    { field: "value", kind: "number" },
    { field: "units", kind: "link", link: "units", latexField: "unitsLatex" },
    { field: "constant", kind: "boolean" },
    DERIVED_UNITS,
  ],
  InitialAssignment: [
    ...ID_COLUMNS,
    { field: "symbol", kind: "link", link: "symbol" },
    MATH,
    DERIVED_UNITS,
  ],
  AssignmentRule: [
    ...ID_COLUMNS,
    { field: "variable", kind: "link", link: "variable" },
    MATH,
    DERIVED_UNITS,
  ],
  RateRule: [
    ...ID_COLUMNS,
    { field: "variable", kind: "link", link: "variable" },
    MATH,
    DERIVED_UNITS,
  ],
  AlgebraicRule: [...ID_COLUMNS, MATH, DERIVED_UNITS],
  Constraint: [...ID_COLUMNS, MATH, { field: "message", kind: "xhtml" }],
  Reaction: [
    ...ID_COLUMNS,
    { field: "reversible", kind: "boolean" },
    { field: "fast", kind: "boolean", onlyWhenTrue: true },
    {
      field: "compartment",
      kind: "link",
      link: "compartment",
      optional: true,
    },
    { field: "equation", kind: "text" },
    {
      field: "fbc.lowerFluxBound",
      kind: "link",
      link: "lowerFluxBound",
      optional: true,
    },
    {
      field: "fbc.upperFluxBound",
      kind: "link",
      link: "upperFluxBound",
      optional: true,
    },
    {
      field: "fbc.geneProductAssociation",
      kind: "geneAssociation",
      optional: true,
    },
    { field: "kineticLaw.math", kind: "math", optional: true },
    {
      field: "kineticLaw.derivedUnits",
      kind: "units",
      latexField: "kineticLaw.derivedUnits",
      optional: true,
    },
  ],
  Event: [
    ...ID_COLUMNS,
    { field: "useValuesFromTriggerTime", kind: "boolean" },
    { field: "trigger.math", kind: "math" },
    { field: "trigger.persistent", kind: "boolean" },
    { field: "trigger.initialValue", kind: "boolean" },
    { field: "priority.math", kind: "math" },
    { field: "delay.math", kind: "math" },
    { field: "listOfEventAssignments", kind: "assignments" },
  ],
};
