import { describe, expect, it } from "vitest";

import { ELEMENT_TYPES } from "@/data/sbmlTypes";
import { COLUMNS, columnsOf, fieldValue, visibleColumns } from "@/report/columns";
import { geneAssociationText, GENE_TEXT_LIMIT } from "@/report/geneAssociation";
import { ReportIndex } from "@/report/index";

import { loadReport } from "./fixtures";

const indexes = [
  new ReportIndex(loadReport("repressilator")),
  new ReportIndex(loadReport("icg_body")),
  new ReportIndex(loadReport("fbc_example")),
  new ReportIndex(loadReport("fbc_constraints_v3")),
  new ReportIndex(loadReport("distrib_uncertainties")),
  new ReportIndex(loadReport("qual_example")),
];
const fbcConstraints = indexes[3]!;
const repressilator = indexes[0]!;

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
              if (column.latexField) {
                const latexHead = column.latexField.split(".")[0]!;
                expect(Object.keys(element), `${type}.${column.latexField}`).toContain(latexHead);
                fieldValue(element, column.latexField);
              }
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
        // an influence column resolves the species of every input or output it renders over
        // the same edge kind, so it names one as well
        if (column.kind === "link" || column.kind === "influence") {
          expect(column.link).toBeDefined();
        }
        if (column.kind !== "link" && column.kind !== "influence") {
          expect(column.link).toBeUndefined();
        }
      }
    }
  });

  it("shows the fbc columns only in a table a row of which fills them", () => {
    const headers = (type: "Species" | "Reaction", index: ReportIndex, model: string) =>
      visibleColumns(type, index.byType(model).get(type) ?? []).map((c) => c.header);
    expect(headers("Species", fbcConstraints, "fbc_constraints_v3")).toContain("formula");
    expect(headers("Species", fbcConstraints, "fbc_constraints_v3")).toContain("charge");
    expect(headers("Reaction", fbcConstraints, "fbc_constraints_v3")).toEqual(
      expect.arrayContaining(["lower bound", "upper bound", "gene association"]),
    );
    // a model without the package keeps the table it had
    expect(headers("Species", repressilator, "BIOMD0000000012")).not.toContain("formula");
    expect(headers("Reaction", repressilator, "BIOMD0000000012")).not.toContain("lower bound");
    // and a column no row of a table fills is left out, whichever package it belongs to: a
    // constraint based model has no kinetic law, a model of amounts no concentration
    expect(headers("Reaction", fbcConstraints, "fbc_constraints_v3")).not.toContain("kinetic law");
    expect(headers("Species", repressilator, "BIOMD0000000012")).not.toContain(
      "initial concentration",
    );
    expect(headers("Species", repressilator, "BIOMD0000000012")).toContain("initial amount");
  });

  it("writes a gene association as the expression it stands for", () => {
    const reaction = fbcConstraints.byType("fbc_constraints_v3").get("Reaction")![0]!;
    const association = (reaction as { fbc?: { geneProductAssociation?: unknown } }).fbc
      ?.geneProductAssociation as { association?: never } | undefined;
    expect(geneAssociationText(association?.association)).toBe("((g_ptsG and g_ptsH) or g_galP)");
    expect(geneAssociationText(null)).toBe("");
    // a wide association is cut off after the first genes, whatever its size
    const wide = {
      pk: "m/Or:wide",
      sbmlType: "Or" as const,
      associations: Array.from({ length: 1000 }, (_, k) => ({
        pk: `m/GeneProductRef:${k}`,
        sbmlType: "GeneProductRef" as const,
        geneProduct: `g${k}`,
      })),
    };
    const text = geneAssociationText(wide);
    expect(text).toContain(`g${GENE_TEXT_LIMIT - 1}`);
    expect(text).not.toContain(`g${GENE_TEXT_LIMIT}`);
    expect(text.endsWith("…)")).toBe(true);
  });

  it("gives a qualitative species its levels and a transition its influences", () => {
    const qual = new ReportIndex(loadReport("qual_example"));
    expect(columnsOf("QualitativeSpecies").map((c) => c.header)).toEqual([
      "id",
      "name",
      "compartment",
      "initial level",
      "max level",
      "constant",
    ]);
    expect(columnsOf("Transition").map((c) => c.header)).toEqual([
      "id",
      "name",
      "inputs",
      "outputs",
      "function terms",
    ]);
    // the cell of the inputs holds the objects, not a string: it renders the species of every
    // one of them as a link with the sign of its influence behind it
    const transition = qual.byType("qual_example").get("Transition")![0]!;
    const inputs = fieldValue(transition, "listOfInputs") as { qualitativeSpecies: string }[];
    expect(inputs.map((input) => input.qualitativeSpecies)).toEqual(["S", "P", "G"]);
    expect(fieldValue(transition, "listOfFunctionTerms.length")).toBe(2);
  });

  it("resolves dotted paths", () => {
    const row = { kineticLaw: { math: { formula: "k" } }, listOfEventAssignments: [1, 2] };
    expect(fieldValue(row, "kineticLaw.math")).toEqual({ formula: "k" });
    expect(fieldValue(row, "listOfEventAssignments.length")).toBe(2);
    expect(fieldValue(row, "nope.deeper")).toBeUndefined();
    expect(fieldValue({ kineticLaw: null }, "kineticLaw.math")).toBeUndefined();
  });
});
