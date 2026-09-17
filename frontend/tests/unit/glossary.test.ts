import { describe, expect, it } from "vitest";

import { COLUMNS } from "@/report/columns";
import { EDGE_KINDS } from "@/data/edgeKinds";
import { DOCUMENT_TYPES, ELEMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { DOCS_URL, attributeEntry, linkEntry, referenceUrl, typeEntry } from "@/report/glossary";

const TYPES = [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES];

describe("glossary", () => {
  it("has an entry for every element type", () => {
    for (const info of TYPES) expect(typeEntry(info.type), info.type).toBeDefined();
  });

  it("has an entry for every column of every table", () => {
    for (const [type, columns] of Object.entries(COLUMNS)) {
      for (const column of columns) {
        expect(
          attributeEntry(type as never, column.field),
          `${type}.${column.field}`,
        ).toBeDefined();
      }
    }
  });

  it("has an entry for every link kind", () => {
    for (const kind of EDGE_KINDS) expect(linkEntry(kind), kind).toBeDefined();
  });

  it("falls back to the shared attributes and to the first segment of a path", () => {
    // Species has no metaId attribute of its own, so this resolves the SBase entry, whose
    // label the glossary keeps as "metaId" (the identifier itself, not a description of it).
    expect(attributeEntry("Species", "metaId")?.label).toBe("metaId");
    // Reaction has no "kineticLaw.math" attribute of its own, so this resolves the dotted
    // "kineticLaw" entry of Reaction (the kinetic law as a whole), not the "math" of KineticLaw.
    expect(attributeEntry("Reaction", "kineticLaw.math")?.label).toBe("kinetic law");
  });

  it("builds the url of a reference page", () => {
    expect(referenceUrl("Species")).toBe(`${DOCS_URL}reference/species/`);
    expect(referenceUrl("Species", "initialAmount")).toBe(
      `${DOCS_URL}reference/species/#initial-amount`,
    );
  });
});
