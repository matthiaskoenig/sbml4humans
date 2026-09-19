import type { ElementType } from "@/api/types";
import { CORE_COLUMNS } from "@/report/columns/core";
import { PACKAGE_COLUMNS } from "@/report/columns/packages";
import type { ColumnDef, ColumnSpec } from "@/report/columns/types";
import { attributeLabel } from "@/report/glossary";

export type { CellKind, ColumnDef, ColumnSpec } from "@/report/columns/types";

const SPECS: Readonly<Record<ElementType, readonly ColumnSpec[]>> = {
  ...CORE_COLUMNS,
  ...PACKAGE_COLUMNS,
};

function headed(type: ElementType): readonly ColumnDef[] {
  return SPECS[type].map((spec) => ({ ...spec, header: attributeLabel(type, spec.field) }));
}

/** The columns of every type, each headed by the name the glossary gives its field. */
export const COLUMNS: Readonly<Record<ElementType, readonly ColumnDef[]>> = {
  FunctionDefinition: headed("FunctionDefinition"),
  UnitDefinition: headed("UnitDefinition"),
  Compartment: headed("Compartment"),
  Species: headed("Species"),
  Parameter: headed("Parameter"),
  InitialAssignment: headed("InitialAssignment"),
  AssignmentRule: headed("AssignmentRule"),
  RateRule: headed("RateRule"),
  AlgebraicRule: headed("AlgebraicRule"),
  Constraint: headed("Constraint"),
  Reaction: headed("Reaction"),
  Event: headed("Event"),
  Submodel: headed("Submodel"),
  Port: headed("Port"),
  GeneProduct: headed("GeneProduct"),
  Objective: headed("Objective"),
  FluxBound: headed("FluxBound"),
  UserDefinedConstraint: headed("UserDefinedConstraint"),
  QualitativeSpecies: headed("QualitativeSpecies"),
  Transition: headed("Transition"),
};

export function columnsOf(type: ElementType): readonly ColumnDef[] {
  return COLUMNS[type];
}

/** The columns a table shows: the optional ones only where a row of the table fills one.
 *
 * The fbc columns of a species and of a reaction are optional, so that a model which does not
 * use the package keeps the table it had, and one which does shows the formula, the charge, the
 * flux bounds and the gene association next to each other. The decision is made over every row
 * of the type, not over the rows a search leaves, so that a column does not come and go while a
 * reader types. */
export function visibleColumns(type: ElementType, rows: readonly object[]): readonly ColumnDef[] {
  const columns = columnsOf(type);
  if (!columns.some((column) => column.optional || column.onlyWhenTrue)) return columns;
  return columns.filter((column) => {
    if (column.onlyWhenTrue) return rows.some((row) => fieldValue(row, column.field) === true);
    if (!column.optional) return true;
    return rows.some((row) => {
      const value = fieldValue(row, column.field);
      return value !== null && value !== undefined && value !== "";
    });
  });
}

/** The value of a dotted path, undefined when a step is missing. */
export function fieldValue(row: object, field: string): unknown {
  let value: unknown = row;
  for (const step of field.split(".")) {
    if (value === null || value === undefined) return undefined;
    value = (value as Record<string, unknown>)[step];
  }
  return value;
}
