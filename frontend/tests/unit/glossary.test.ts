import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";

import { describe, expect, it } from "vitest";

import type { SbmlType } from "@/api/types";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import { COLUMNS } from "@/report/columns";
import { EDGE_KINDS } from "@/data/edgeKinds";
import {
  DOCS_URL,
  attributeEntry,
  attributeKey,
  attributeLabel,
  conceptEntry,
  conceptKey,
  entryOfKey,
  linkEntry,
  linkKey,
  referenceUrl,
  typeEntry,
  typeKey,
} from "@/report/glossary";

import { ATTRIBUTES_DIR, TYPES, modelUnitFields, staticFields } from "./glossaryFields";

/** The rows of a component's source which state both a static `field="..."` and a static
 * `label="..."`: the glossary names the field of such a row, and the label overrides that name. */
function labelledFields(source: string): { field: string; label: string }[] {
  return [...source.matchAll(/<AttributeRow\b[^>]*>/g)].flatMap((tag) => {
    const field = tag[0].match(/(?<!:)\bfield="([^"]+)"/)?.[1];
    const label = tag[0].match(/(?<!:)\blabel="([^"]+)"/)?.[1];
    return field && label ? [{ field, label }] : [];
  });
}

/** The name of an attribute as a specification writes it: one word in camel case, behind the
 * prefix of its package where a package adds the attribute to a core type (`fbc:charge`). The
 * check of the glossary holds every attribute which cites a specification to the same pattern. */
const SPECIFICATION_NAME = /^([a-z]+:)?[A-Za-z][A-Za-z0-9]*$/;

/** The columns of a field which the report adds and no specification names, under the plain
 * words which head them. */
const REPORT_COLUMNS: Readonly<Record<string, string>> = {
  derivedUnits: "derived units",
  "kineticLaw.derivedUnits": "derived units",
  unitsLatex: "formula",
  equation: "equation",
};

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
    // label is the name of the attribute in the specification, "metaid", and not the name of
    // the field of the report, "metaId".
    expect(attributeEntry("Species", "metaId")?.label).toBe("metaid");
    // Submodel has no "listOfDeletions.length" attribute of its own, and the count column
    // does not need one: falling back to the first segment "listOfDeletions" resolves the
    // entry of the list the column counts, which describes the same thing at the list level.
    expect(attributeEntry("Submodel", "listOfDeletions.length")?.label).toBe("listOfDeletions");
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
      const fields = staticFields(source).concat(
        (type === "Model" ? modelUnitFields(source) : []).map((field) => ({ field, type: null })),
      );
      // fails just as loudly when a component's fields cannot be extracted at all
      expect(fields.length, `${type}Attributes.vue`).toBeGreaterThan(0);
      for (const { field, type: rowType } of fields) {
        const owner = rowType ?? type;
        expect(attributeEntry(owner, field), `${owner}.${field}`).toBeDefined();
      }
    }

    // AttributesColumn.vue renders the same handful of SBase level rows (metaId, sbo, the comp
    // replacement rows, the uncertainties row) for every type, so every type has to resolve them.
    const shared = staticFields(
      readFileSync(join(ATTRIBUTES_DIR, "..", "AttributesColumn.vue"), "utf8"),
    );
    expect(shared.length).toBeGreaterThan(0);
    for (const type of types) {
      for (const { field } of shared) {
        expect(attributeEntry(type, field), `${type}.${field} (AttributesColumn)`).toBeDefined();
      }
    }
  });

  it("names every row of the inspector by the glossary", () => {
    // a row with a field takes its name from the glossary, so that the inspector, the tables and
    // the reference name an attribute alike; a label next to a field would be a second name
    const inspectorDir = join(ATTRIBUTES_DIR, "..");
    const components = readdirSync(inspectorDir, { recursive: true, encoding: "utf8" }).filter(
      (file) => file.endsWith(".vue"),
    );
    expect(components.length).toBeGreaterThan(Object.keys(ATTRIBUTE_COMPONENTS).length);
    const labelled = components.flatMap((file) =>
      labelledFields(readFileSync(join(inspectorDir, file), "utf8")).map(
        ({ field, label }) =>
          `${relative(ATTRIBUTES_DIR, join(inspectorDir, file))}: ${field} as "${label}"`,
      ),
    );
    // the one exception: a submodel shows the model its external model definition resolves to,
    // a field of another type, under a name which says whose model it is
    expect(labelled).toEqual(['SubmodelAttributes.vue: resolution.model as "external model"']);
  });

  it("heads every column of a table by the name the glossary gives its field", () => {
    for (const [type, columns] of Object.entries(COLUMNS)) {
      for (const column of columns) {
        const where = `${type}.${column.field}`;
        expect(column.header, where).toBe(attributeLabel(type as SbmlType, column.field));
        const words = REPORT_COLUMNS[column.field];
        if (words === undefined) {
          // an attribute of a specification is headed by its name there, never by words
          expect(column.header, where).toMatch(SPECIFICATION_NAME);
        } else {
          expect(column.header, where).toBe(words);
        }
      }
    }
    expect(COLUMNS.Species.map((column) => column.header)).toEqual(
      expect.arrayContaining(["initialConcentration", "hasOnlySubstanceUnits", "fbc:charge"]),
    );
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

  it("keys a type, a link kind and a concept it has an entry for", () => {
    expect(typeKey("Species")).toBe("types/Species");
    expect(linkKey("compartment")).toBe("links/compartment");
    expect(conceptKey("derivedUnits")).toBe(
      conceptEntry("derivedUnits") && "concepts/derivedUnits",
    );
  });

  it("keys an attribute through the same resolution attributeEntry uses", () => {
    // Species has its own "compartment" attribute
    expect(attributeKey("Species", "compartment")).toBe("types/Species/compartment");
    // Species has no metaId of its own, so the key names the SBase entry it falls back to
    expect(attributeKey("Species", "metaId")).toBe("types/SBase/metaId");
    // Submodel has no "listOfDeletions.length" of its own, so the key names the first segment
    expect(attributeKey("Submodel", "listOfDeletions.length")).toBe(
      "types/Submodel/listOfDeletions",
    );
    // Reaction has its own "kineticLaw.derivedUnits" entry, not the first segment fallback
    expect(attributeKey("Reaction", "kineticLaw.derivedUnits")).toBe(
      "types/Reaction/kineticLaw.derivedUnits",
    );
    expect(attributeKey("Species", "nope")).toBeUndefined();
  });

  it("answers entryOfKey with the label and summary a key's own lookup would give", () => {
    expect(entryOfKey("types/Species")).toEqual(typeEntry("Species"));
    expect(entryOfKey("types/Species/compartment")).toEqual(
      attributeEntry("Species", "compartment"),
    );
    expect(entryOfKey("types/Species/fbc.charge")).toEqual(attributeEntry("Species", "fbc.charge"));
    expect(entryOfKey("links/compartment")).toEqual(linkEntry("compartment"));
    expect(entryOfKey("concepts/derivedUnits")).toEqual(conceptEntry("derivedUnits"));
    // the eager glossary has no data types, the dialog falls back to the last segment of the key
    expect(entryOfKey("datatypes/SId")).toBeUndefined();
    expect(entryOfKey("nope")).toBeUndefined();
  });
});
