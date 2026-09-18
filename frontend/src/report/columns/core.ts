import type { ElementType } from "@/api/types";
import { ID_COLUMNS, type ColumnDef } from "@/report/columns/types";

const MATH: ColumnDef = { field: "math", header: "math", kind: "math" };
const DERIVED_UNITS: ColumnDef = {
  field: "derivedUnits",
  header: "derived units",
  kind: "units",
  latexField: "derivedUnits",
};

type CoreType = Exclude<
  ElementType,
  "Submodel" | "Port" | "GeneProduct" | "Objective" | "FluxBound"
>;

export const CORE_COLUMNS: Readonly<Record<CoreType, readonly ColumnDef[]>> = {
  FunctionDefinition: [...ID_COLUMNS, MATH],
  UnitDefinition: [
    ...ID_COLUMNS,
    { field: "unitsLatex", header: "units", kind: "units", latexField: "unitsLatex" },
  ],
  Compartment: [
    ...ID_COLUMNS,
    { field: "spatialDimensions", header: "dimensions", kind: "number" },
    { field: "size", header: "size", kind: "number" },
    { field: "units", header: "units", kind: "link", link: "units", latexField: "unitsLatex" },
    { field: "constant", header: "constant", kind: "boolean" },
    DERIVED_UNITS,
  ],
  Species: [
    ...ID_COLUMNS,
    { field: "compartment", header: "compartment", kind: "link", link: "compartment" },
    { field: "initialAmount", header: "initial amount", kind: "number" },
    { field: "initialConcentration", header: "initial concentration", kind: "number" },
    {
      field: "substanceUnits",
      header: "substance units",
      kind: "link",
      link: "units",
      latexField: "unitsLatex",
    },
    { field: "hasOnlySubstanceUnits", header: "only substance units", kind: "boolean" },
    { field: "boundaryCondition", header: "boundary condition", kind: "boolean" },
    { field: "constant", header: "constant", kind: "boolean" },
    DERIVED_UNITS,
  ],
  Parameter: [
    ...ID_COLUMNS,
    { field: "value", header: "value", kind: "number" },
    { field: "units", header: "units", kind: "link", link: "units", latexField: "unitsLatex" },
    { field: "constant", header: "constant", kind: "boolean" },
    DERIVED_UNITS,
  ],
  InitialAssignment: [
    ...ID_COLUMNS,
    { field: "symbol", header: "symbol", kind: "link", link: "symbol" },
    MATH,
    DERIVED_UNITS,
  ],
  AssignmentRule: [
    ...ID_COLUMNS,
    { field: "variable", header: "variable", kind: "link", link: "variable" },
    MATH,
    DERIVED_UNITS,
  ],
  RateRule: [
    ...ID_COLUMNS,
    { field: "variable", header: "variable", kind: "link", link: "variable" },
    MATH,
    DERIVED_UNITS,
  ],
  AlgebraicRule: [...ID_COLUMNS, MATH, DERIVED_UNITS],
  Constraint: [...ID_COLUMNS, MATH, { field: "message", header: "message", kind: "xhtml" }],
  Reaction: [
    ...ID_COLUMNS,
    { field: "reversible", header: "reversible", kind: "boolean" },
    { field: "fast", header: "fast", kind: "boolean" },
    { field: "compartment", header: "compartment", kind: "link", link: "compartment" },
    { field: "equation", header: "equation", kind: "text" },
    { field: "kineticLaw.math", header: "kinetic law", kind: "math" },
    {
      field: "kineticLaw.derivedUnits",
      header: "derived units",
      kind: "units",
      latexField: "kineticLaw.derivedUnits",
    },
  ],
  Event: [
    ...ID_COLUMNS,
    { field: "useValuesFromTriggerTime", header: "values from trigger time", kind: "boolean" },
    { field: "trigger.math", header: "trigger", kind: "math" },
    { field: "trigger.persistent", header: "persistent", kind: "boolean" },
    { field: "trigger.initialValue", header: "initial value", kind: "boolean" },
    { field: "priority.math", header: "priority", kind: "math" },
    { field: "delay.math", header: "delay", kind: "math" },
    { field: "listOfEventAssignments", header: "assignments", kind: "assignments" },
  ],
};
