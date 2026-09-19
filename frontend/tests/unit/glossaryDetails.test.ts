import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import type { SbmlType } from "@/api/types";
import { ATTRIBUTE_COMPONENTS } from "@/components/inspector/attributes";
import { EDGE_KINDS } from "@/data/edgeKinds";
import { COLUMNS } from "@/report/columns";
import { attributeKey, linkKey, typeKey } from "@/report/glossary";
import { loadGlossaryDetails, type GlossaryDetails } from "@/report/glossaryDetails";

import { ATTRIBUTES_DIR, TYPES, modelUnitFields, staticFields } from "./glossaryFields";

// read with readFileSync, not through `loadGlossaryDetails`: the loader's dynamic `import()` is
// the only reference to the json the production bundle may carry, and a static import here, for
// a file this size, would pull the details back into the same chunk as everything else.
const DETAILS_PATH = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "src",
  "data",
  "glossary-details.json",
);
const details = JSON.parse(readFileSync(DETAILS_PATH, "utf8")) as GlossaryDetails;
const keys = new Set(Object.keys(details.entries));

/** Every `glossary:<key>` target a markdown description links to. */
function glossaryLinks(description: string): string[] {
  return [...description.matchAll(/\]\(glossary:([^)]+)\)/g)].map((match) => match[1]!);
}

describe("glossary details", () => {
  it("has a key for every element type", () => {
    for (const info of TYPES) {
      const key = typeKey(info.type);
      expect(key, info.type).toBeDefined();
      expect(keys.has(key!), `${info.type} -> ${key}`).toBe(true);
    }
  });

  it("has a key for every link kind", () => {
    for (const kind of EDGE_KINDS) {
      const key = linkKey(kind);
      expect(key, kind).toBeDefined();
      expect(keys.has(key!), `${kind} -> ${key}`).toBe(true);
    }
  });

  it("has a key for every column of every table", () => {
    for (const [type, columns] of Object.entries(COLUMNS)) {
      for (const column of columns) {
        const key = attributeKey(type as never, column.field);
        expect(key, `${type}.${column.field}`).toBeDefined();
        expect(keys.has(key!), `${type}.${column.field} -> ${key}`).toBe(true);
      }
    }
  });

  it("has a key for every field an inspector attribute component passes to AttributeRow", () => {
    const types = Object.keys(ATTRIBUTE_COMPONENTS) as SbmlType[];
    for (const type of types) {
      const source = readFileSync(join(ATTRIBUTES_DIR, `${type}Attributes.vue`), "utf8");
      const fields = staticFields(source).concat(
        (type === "Model" ? modelUnitFields(source) : []).map((field) => ({ field, type: null })),
      );
      for (const { field, type: rowType } of fields) {
        const owner = rowType ?? type;
        const key = attributeKey(owner, field);
        expect(key, `${owner}.${field}`).toBeDefined();
        expect(keys.has(key!), `${owner}.${field} -> ${key}`).toBe(true);
      }
    }

    const shared = staticFields(
      readFileSync(join(ATTRIBUTES_DIR, "..", "AttributesColumn.vue"), "utf8"),
    );
    for (const type of types) {
      for (const { field } of shared) {
        const key = attributeKey(type, field);
        expect(key, `${type}.${field} (AttributesColumn)`).toBeDefined();
        expect(keys.has(key!), `${type}.${field} -> ${key} (AttributesColumn)`).toBe(true);
      }
    }
  });

  it("has a key for every attribute the eager glossary itself lists", async () => {
    // the eager glossary of `glossary.ts`, read once through the module (it is small and is
    // already imported statically all over the frontend, unlike the details).
    const rawGlossary = (await import("@/data/glossary.json")).default as {
      types: Record<string, { attributes: Record<string, unknown> }>;
    };
    for (const [type, typeEntry] of Object.entries(rawGlossary.types)) {
      for (const field of Object.keys(typeEntry.attributes)) {
        const key = attributeKey(type as SbmlType, field);
        expect(key, `${type}.${field}`).toBeDefined();
        expect(keys.has(key!), `${type}.${field} -> ${key}`).toBe(true);
      }
    }
  });

  it("resolves every reference an entry of the details makes to another one", () => {
    for (const [key, entry] of Object.entries(details.entries)) {
      if (entry.owner !== undefined) {
        expect(keys.has(entry.owner), `${key}: owner ${entry.owner}`).toBe(true);
      }
      if (entry.type !== undefined) {
        expect(keys.has(entry.type.key), `${key}: type.key ${entry.type.key}`).toBe(true);
      }
      for (const related of entry.related ?? []) {
        expect(keys.has(related), `${key}: related ${related}`).toBe(true);
      }
      for (const attribute of entry.attributes ?? []) {
        expect(keys.has(attribute), `${key}: attributes ${attribute}`).toBe(true);
      }
      for (const target of glossaryLinks(entry.description)) {
        expect(keys.has(target), `${key}: description links to ${target}`).toBe(true);
      }
    }
  });
});

describe("loadGlossaryDetails", () => {
  it("returns the same promise twice", () => {
    expect(loadGlossaryDetails()).toBe(loadGlossaryDetails());
  });

  it("resolves the entries of the details json", async () => {
    const loaded = await loadGlossaryDetails();
    expect(loaded.entries["types/Species"]?.label).toBe("Species");
    expect(loaded.entries["types/Species"]?.kind).toBe("type");
  });
});
