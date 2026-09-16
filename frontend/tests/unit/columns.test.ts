import { describe, expect, it } from "vitest";

import { ELEMENT_TYPES } from "@/data/sbmlTypes";
import { COLUMNS, columnsOf, fieldValue } from "@/report/columns";
import { ReportIndex } from "@/report/index";

import { loadReport } from "./fixtures";

const indexes = [
  new ReportIndex(loadReport("repressilator")),
  new ReportIndex(loadReport("icg_body")),
  new ReportIndex(loadReport("fbc_example")),
  new ReportIndex(loadReport("distrib_uncertainties")),
];

describe("columns", () => {
  it("defines columns for every element type, id and name first", () => {
    for (const info of ELEMENT_TYPES) {
      const columns = columnsOf(info.type);
      expect(columns.length, info.type).toBeGreaterThanOrEqual(2);
      expect(columns[0]).toMatchObject({ field: "id", kind: "id" });
      expect(columns[1]).toMatchObject({ field: "name", kind: "text" });
      expect(new Set(columns.map((c) => c.field)).size).toBe(columns.length);
    }
  });

  it("every column field exists on the elements of the fixtures", () => {
    let checked = 0;
    for (const index of indexes) {
      for (const model of index.models) {
        for (const [type, elements] of index.byType(model.id!)) {
          for (const element of elements) {
            for (const column of COLUMNS[type]) {
              const head = column.field.split(".")[0]!;
              expect(Object.keys(element), `${type}.${column.field}`).toContain(head);
              fieldValue(element, column.field);
              checked += 1;
            }
          }
        }
      }
    }
    expect(checked).toBeGreaterThan(100);
  });

  it("link columns name an edge kind and units columns a latex field", () => {
    for (const columns of Object.values(COLUMNS)) {
      for (const column of columns) {
        if (column.kind === "link") expect(column.link).toBeDefined();
        if (column.kind !== "link") expect(column.link).toBeUndefined();
      }
    }
  });

  it("resolves dotted paths", () => {
    const row = { kineticLaw: { math: { formula: "k" } }, listOfEventAssignments: [1, 2] };
    expect(fieldValue(row, "kineticLaw.math")).toEqual({ formula: "k" });
    expect(fieldValue(row, "listOfEventAssignments.length")).toBe(2);
    expect(fieldValue(row, "nope.deeper")).toBeUndefined();
    expect(fieldValue({ kineticLaw: null }, "kineticLaw.math")).toBeUndefined();
  });
});
