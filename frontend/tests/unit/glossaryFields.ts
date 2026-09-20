import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import type { SbmlType } from "@/api/types";
import { DOCUMENT_TYPES, ELEMENT_TYPES, NESTED_TYPES } from "@/data/sbmlTypes";

/** Every type the report shows, document, element and nested types together: the types
 * `glossary.test.ts` and `glossaryDetails.test.ts` both demand an entry, and a key, for. */
export const TYPES = [...DOCUMENT_TYPES, ...ELEMENT_TYPES, ...NESTED_TYPES];

// tests/unit -> src/components/inspector/attributes, the directory of the 25 components these
// helpers read as plain text, since importing and mounting all of them just to look at their
// props would be slower and would not see an unused `field` the way a source read does.
export const ATTRIBUTES_DIR = join(
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
export function staticFields(source: string): { field: string; type: SbmlType | null }[] {
  return [...source.matchAll(/<AttributeRow\b[^>]*>/g)].flatMap((tag) => {
    const field = tag[0].match(/(?<!:)\bfield="([^"]+)"/)?.[1];
    // a row names the type of its field where it is not the type of the component: a submodel
    // shows the model its external model definition resolves to
    const type = tag[0].match(/(?<!:)\btype="([^"]+)"/)?.[1] as SbmlType | undefined;
    return field ? [{ field, type: type ?? null }] : [];
  });
}

/** `ModelAttributes.vue` binds `:field="idKey"` in a `v-for` over its `UNITS` table instead of
 * writing six field props out by hand; this reads the second column of that table ("substance",
 * "substanceUnits", "substanceUnitsLatex" -> "substanceUnits"), the one `staticFields` cannot see. */
export function modelUnitFields(source: string): string[] {
  const table = source.match(/const UNITS = \[([\s\S]*?)\] as const;/)?.[1] ?? "";
  return [...table.matchAll(/\[\s*"[^"]*",\s*"([^"]+)"/g)].map((match) => match[1]!);
}
