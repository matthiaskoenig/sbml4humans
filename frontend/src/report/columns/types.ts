import type { EdgeKind } from "@/api/types";

export type CellKind = "id" | "text" | "number" | "boolean" | "math" | "units" | "link" | "count";

/** One column of an element table. */
export interface ColumnDef {
  /** Dotted path into the row, also the sort field. */
  field: string;
  header: string;
  kind: CellKind;
  /** Kind "link": the edge kind that resolves the referenced element. */
  link?: EdgeKind;
  /** Kind "units" and kind "link" with `link: "units"`: the field holding the latex of the
   * units, default `${field}Latex`. */
  latexField?: string;
  width?: string;
}

export const ID_COLUMNS: readonly ColumnDef[] = [
  { field: "id", header: "id", kind: "id", width: "12rem" },
  { field: "name", header: "name", kind: "text", width: "14rem" },
];
