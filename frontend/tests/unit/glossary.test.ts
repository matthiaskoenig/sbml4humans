import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import type { SbmlType } from "@/api/types";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import { COLUMNS } from "@/report/columns";
import { EDGE_KINDS } from "@/data/edgeKinds";
import { DOCUMENT_TYPES, ELEMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";
import { DOCS_URL, attributeEntry, linkEntry, referenceUrl, typeEntry } from "@/report/glossary";

const TYPES = [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES];

// tests/unit -> src/components/inspector/attributes, the directory of the 25 components this
// test reads as plain text, since importing and mounting all of them just to look at their
// props would be slower and would not see an unused `field` the way a source read does.
const ATTRIBUTES_DIR = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "src",
  "components",
  "inspector",
  "attributes",
);

/** The static `field="..."` values a component's source passes to `AttributeRow`. A
 * `:field="..."` bound to a variable, not a plain string, is not a field name and is excluded,
 * so a component looping over a local array (see `modelUnitFields`) needs its own extractor. */
function staticFields(source: string): string[] {
  return [...source.matchAll(/(?<!:)\bfield="([^"]+)"/g)].map((match) => match[1]!);
}

/** `ModelAttributes.vue` binds `:field="idKey"` in a `v-for` over its `UNITS` table instead of
 * writing six field props out by hand; this reads the second column of that table ("substance",
 * "substanceUnits", "substanceUnitsLatex" -> "substanceUnits"), the one `staticFields` cannot see. */
function modelUnitFields(source: string): string[] {
  const table = source.match(/const UNITS = \[([\s\S]*?)\] as const;/)?.[1] ?? "";
  return [...table.matchAll(/\[\s*"[^"]*",\s*"([^"]+)"/g)].map((match) => match[1]!);
}

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
    // Submodel has no "listOfDeletions.length" attribute of its own, and the count column
    // does not need one: falling back to the first segment "listOfDeletions" resolves the
    // entry of the list the column counts, which describes the same thing at the list level.
    expect(attributeEntry("Submodel", "listOfDeletions.length")?.label).toBe("deletions");
  });

  it("does not fall back where the fallback would mislead", () => {
    // Reaction has its own "kineticLaw" entry (the kinetic law as a whole, for the inspector
    // row), which used to catch these two dotted report columns by the first segment fallback
    // and show its summary ("the formula which gives the speed of the reaction") under both
    // headers, including "derived units". Both dotted columns now have their own entry.
    expect(attributeEntry("Reaction", "kineticLaw.math")?.summary).not.toBe(
      attributeEntry("Reaction", "kineticLaw")?.summary,
    );
    expect(attributeEntry("Reaction", "kineticLaw.derivedUnits")?.summary).not.toBe(
      attributeEntry("Reaction", "kineticLaw")?.summary,
    );
    expect(attributeEntry("Reaction", "kineticLaw.derivedUnits")?.label).toBe("derived units");
  });

  it("has an entry for every field an inspector attribute component passes to AttributeRow", () => {
    const types = Object.keys(ATTRIBUTE_COMPONENTS) as SbmlType[];
    for (const type of types) {
      const source = readFileSync(join(ATTRIBUTES_DIR, `${type}Attributes.vue`), "utf8");
      const fields = staticFields(source).concat(type === "Model" ? modelUnitFields(source) : []);
      // fails just as loudly when a component's fields cannot be extracted at all
      expect(fields.length, `${type}Attributes.vue`).toBeGreaterThan(0);
      for (const fieldName of fields) {
        expect(attributeEntry(type, fieldName), `${type}.${fieldName}`).toBeDefined();
      }
    }

    // AttributesColumn.vue renders the same handful of SBase level rows (metaId, sbo, the comp
    // replacement rows, the uncertainties row) for every type, so every type has to resolve them.
    const shared = staticFields(
      readFileSync(join(ATTRIBUTES_DIR, "..", "AttributesColumn.vue"), "utf8"),
    );
    expect(shared.length).toBeGreaterThan(0);
    for (const type of types) {
      for (const fieldName of shared) {
        expect(
          attributeEntry(type, fieldName),
          `${type}.${fieldName} (AttributesColumn)`,
        ).toBeDefined();
      }
    }
  });

  it("builds the url of a reference page", () => {
    // the page of the type, which the inspector links; the anchors of the attributes are used
    // by the links inside the site, not by the application
    expect(referenceUrl("Species")).toBe(`${DOCS_URL}reference/species/`);
    expect(referenceUrl("Reaction")).toBe(`${DOCS_URL}reference/reaction/`);
  });

  it("explains a link kind in every context in which a group of it is shown", () => {
    // the compartment of a qualitative species is a group of the same kind as the compartment of
    // a species, and the bounds of a user defined constraint bound a sum, not a flux
    expect(linkEntry("compartment")?.summary).toContain("qualitative species");
    expect(linkEntry("lowerBound")?.summary).toContain("user defined constraint");
    expect(linkEntry("lowerBound")?.summary).not.toContain("flux");
  });
});
