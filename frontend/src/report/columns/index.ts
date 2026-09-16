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

/** The value of a dotted path, undefined when a step is missing. */
export function fieldValue(row: object, field: string): unknown {
  let value: unknown = row;
  for (const step of field.split(".")) {
    if (value === null || value === undefined) return undefined;
    value = (value as Record<string, unknown>)[step];
  }
  return value;
}
