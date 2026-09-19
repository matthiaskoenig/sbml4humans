import type { EdgeKind } from "@/api/types";

export type CellKind =
  | "id"
  | "text"
  | "number"
  | "boolean"
  | "math"
  | "units"
  | "link"
  | "count"
  | "assignments"
  | "terms"
  | "elements"
  | "geneAssociation"
  | "influence"
  | "xhtml";

/** What a column of an element table is defined by. It states no header: a column is headed by
 * the name the glossary gives its field, the name of the attribute in the specification, so that
 * a table, the inspector and the reference name an attribute alike. */
export interface ColumnSpec {
  /** Dotted path into the row, also the sort field. */
  field: string;
  kind: CellKind;
  /** Kind "link": the edge kind that resolves the referenced element. Kind "influence": the
   * edge kind that resolves the qualitative species of every input or output of the cell. */
  link?: EdgeKind;
  /** Kind "units" and kind "link" with `link: "units"`: the field holding the latex of the
   * units, default `${field}Latex`. */
  latexField?: string;
  width?: string;
  /** A column which is left out of a table no row of which fills it: the fbc columns of a
   * species or a reaction of a model which does not use the package. */
  optional?: boolean;
  /** A boolean column which is left out of a table no row of which sets it to true. `fast` is
   * the one: a Level 2 file gives every reaction the default false of its specification, Level 3
   * Version 2 dropped the attribute, and a column of that default says nothing, while a single
   * fast reaction is exactly what a reader has to see. */
  onlyWhenTrue?: boolean;
}

export const ID_COLUMNS: readonly ColumnSpec[] = [
  { field: "id", kind: "id", width: "12rem" },
  { field: "name", kind: "text", width: "14rem" },
];

/** One column of an element table: what defines it, under the header of its field. */
export interface ColumnDef extends ColumnSpec {
  header: string;
}
