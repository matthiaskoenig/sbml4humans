import { describe, expect, it } from "vitest";

import { compareValues, isEmptyValue, sortRows } from "@/report/sort";

describe("sort", () => {
  it("knows the empty values", () => {
    for (const value of [null, undefined, "", [], {}]) expect(isEmptyValue(value)).toBe(true);
    for (const value of [0, false, "a", [1], { a: 1 }, new Date(0)]) {
      expect(isEmptyValue(value)).toBe(false);
    }
  });

  it("sorts strings with numeric collation in both orders", () => {
    const rows = [{ id: "x10" }, { id: "x2" }, { id: "X1" }];
    expect(sortRows(rows, { field: "id", order: 1 }).map((row) => row.id)).toEqual([
      "X1",
      "x2",
      "x10",
    ]);
    expect(sortRows(rows, { field: "id", order: -1 }).map((row) => row.id)).toEqual([
      "x10",
      "x2",
      "X1",
    ]);
  });

  it("puts the empty values last in both orders", () => {
    const rows = [{ v: null }, { v: 2 }, { v: undefined }, { v: 1 }, { v: "" }];
    expect(sortRows(rows, { field: "v", order: 1 }).map((row) => row.v)).toEqual([
      1,
      2,
      null,
      undefined,
      "",
    ]);
    expect(sortRows(rows, { field: "v", order: -1 }).map((row) => row.v)).toEqual([
      2,
      1,
      null,
      undefined,
      "",
    ]);
  });

  it("compares numbers and booleans by value", () => {
    expect(compareValues(2, 10, 1)).toBeLessThan(0);
    expect(compareValues(2, 10, -1)).toBeGreaterThan(0);
    expect(compareValues(false, true, 1)).toBeLessThan(0);
    expect(compareValues(3, 3, 1)).toBe(0);
  });

  it("keeps the order of equal values and reads nested fields", () => {
    const rows = [
      { pk: "a", comp: { size: 2 } },
      { pk: "b", comp: { size: 1 } },
      { pk: "c", comp: { size: 2 } },
    ];
    expect(sortRows(rows, { field: "comp.size", order: 1 }).map((row) => row.pk)).toEqual([
      "b",
      "a",
      "c",
    ]);
    expect(sortRows(rows, { field: "comp.size", order: -1 }).map((row) => row.pk)).toEqual([
      "a",
      "c",
      "b",
    ]);
  });

  it("returns a copy in the order of the report without a sort", () => {
    const rows = [{ id: "b" }, { id: "a" }];
    const sorted = sortRows(rows, null);
    expect(sorted).toEqual(rows);
    expect(sorted).not.toBe(rows);
  });
});
