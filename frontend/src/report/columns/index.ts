import type { ElementType } from "@/api/types";
import { CORE_COLUMNS } from "@/report/columns/core";
import { PACKAGE_COLUMNS } from "@/report/columns/packages";
import type { ColumnDef } from "@/report/columns/types";

export type { CellKind, ColumnDef } from "@/report/columns/types";

export const COLUMNS: Readonly<Record<ElementType, readonly ColumnDef[]>> = {
  ...CORE_COLUMNS,
  ...PACKAGE_COLUMNS,
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
  if (!columns.some((column) => column.optional)) return columns;
  return columns.filter(
    (column) =>
      !column.optional ||
      rows.some((row) => {
        const value = fieldValue(row, column.field);
        return value !== null && value !== undefined && value !== "";
      }),
  );
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
