import { fieldValue } from "@/report/columns";
import { toNumber } from "@/report/number";

export type SortOrder = 1 | -1;

/** The sort of an element table: one column, ascending (1) or descending (-1). */
export interface SortState {
  field: string;
  order: SortOrder;
}

const collator = new Intl.Collator(undefined, { numeric: true });

/** Empty for the sort: null, undefined, the empty string, an empty array or object. */
export function isEmptyValue(value: unknown): boolean {
  if (value === null || value === undefined || value === "") return true;
  if (Array.isArray(value)) return value.length === 0;
  return typeof value === "object" && !(value instanceof Date) && Object.keys(value).length === 0;
}

/** Compare two values of a column for `order`: empty values last in both orders, doubles as the
 * numbers they stand for, with a value which is not a number last the way an empty one is,
 * strings with numeric collation (`x2` before `x10`), every other value with `<` and `>`. */
export function compareValues(a: unknown, b: unknown, order: SortOrder): number {
  const emptyA = isEmptyValue(a);
  const emptyB = isEmptyValue(b);
  if (emptyA || emptyB) return emptyA === emptyB ? 0 : emptyA ? 1 : -1;
  // an infinite value reaches the frontend as a string, and it sorts where the number it
  // stands for belongs, at the end of the column
  const numberA = toNumber(a);
  const numberB = toNumber(b);
  if (numberA !== null && numberB !== null) {
    const nanA = Number.isNaN(numberA);
    const nanB = Number.isNaN(numberB);
    if (nanA || nanB) return nanA === nanB ? 0 : nanA ? 1 : -1;
    return order * (numberA < numberB ? -1 : numberA > numberB ? 1 : 0);
  }
  if (typeof a === "string" && typeof b === "string") return order * collator.compare(a, b);
  const x = a as number;
  const y = b as number;
  return order * (x < y ? -1 : x > y ? 1 : 0);
}

/** The rows sorted by `sort` (stable), a copy in the order of the report without a sort. The
 * value of a row is its field, or what `valueOf` makes of it: the id column of an element table
 * sorts a row the file gives no id by the name the report gives it. */
export function sortRows<T extends object>(
  rows: readonly T[],
  sort: SortState | null,
  valueOf: (row: T, field: string) => unknown = fieldValue,
): T[] {
  if (!sort) return [...rows];
  const values = new Map(rows.map((row) => [row, valueOf(row, sort.field)]));
  return [...rows].sort((a, b) => compareValues(values.get(a), values.get(b), sort.order));
}
