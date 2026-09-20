import rawGlossary from "@/data/glossary.json";

import type { EdgeKind, SbmlType } from "@/api/types";

export interface GlossaryEntry {
  label: string;
  summary: string;
}

/** A type entry of the glossary: the shared `SBase` entry and the three package entries
 * (`comp`, `fbc`, `distrib`) carry the same shape but are not offered as an element type. */
interface TypeGlossaryEntry extends GlossaryEntry {
  package: string;
  page: string;
  attributes: Record<string, GlossaryEntry>;
}

interface Glossary {
  types: Record<string, TypeGlossaryEntry>;
  links: Record<string, GlossaryEntry>;
  concepts: Record<string, GlossaryEntry>;
}

const glossary = rawGlossary as Glossary;

/** The base url of the documentation site, e.g. to build the url of a reference page.
 * Vitest does not load `.env.development`, so an unset and an empty `VITE_DOCS_URL` both fall
 * back to the site's own default instead of building a relative, broken link. */
export const DOCS_URL: string =
  (import.meta.env.VITE_DOCS_URL as string | undefined)?.trim() ||
  "https://matthiaskoenig.github.io/sbml4humans/";

export function typeEntry(type: SbmlType): GlossaryEntry | undefined {
  return glossary.types[type];
}

/** The key of a type, `types/<Type>`, `undefined` where the type has no entry. A dialog opens on
 * this key; a caller which gets `undefined` renders a plain, unclickable label instead. */
export function typeKey(type: SbmlType): string | undefined {
  return typeEntry(type) ? `types/${type}` : undefined;
}

/** The first segment of a dotted field, e.g. "kineticLaw" of "kineticLaw.math". */
function firstSegment(field: string): string {
  const dot = field.indexOf(".");
  return dot === -1 ? field : field.slice(0, dot);
}

/** The entry of a field of a type, resolved through the same chain `attributeKey` reads its key
 * from: the exact field on the type, then the exact field on the shared `SBase` attributes, then
 * the first segment of a dotted field on the type, then the first segment on `SBase`. The owner
 * and the name it returns are which of the two types matched and under which name, so that the
 * key `types/<owner>/<name>` a label opens a dialog on is always the entry that label shows. */
function resolveAttribute(
  type: SbmlType,
  field: string,
): { owner: string; name: string; entry: GlossaryEntry } | undefined {
  const typeAttributes = glossary.types[type]?.attributes;
  const sbaseAttributes = glossary.types.SBase?.attributes;
  if (typeAttributes?.[field]) return { owner: type, name: field, entry: typeAttributes[field] };
  if (sbaseAttributes?.[field])
    return { owner: "SBase", name: field, entry: sbaseAttributes[field] };
  const segment = firstSegment(field);
  if (segment === field) return undefined;
  if (typeAttributes?.[segment])
    return { owner: type, name: segment, entry: typeAttributes[segment] };
  if (sbaseAttributes?.[segment]) {
    return { owner: "SBase", name: segment, entry: sbaseAttributes[segment] };
  }
  return undefined;
}

export function attributeEntry(type: SbmlType, field: string): GlossaryEntry | undefined {
  return resolveAttribute(type, field)?.entry;
}

/** The key of a field of a type, `types/<owner>/<name>`, resolved by the same chain as
 * `attributeEntry` so that a label and the dialog it opens can never disagree about which entry
 * explains the field. `undefined` where nothing in the chain resolves. */
export function attributeKey(type: SbmlType, field: string): string | undefined {
  const resolved = resolveAttribute(type, field);
  return resolved ? `types/${resolved.owner}/${resolved.name}` : undefined;
}

/** The name of a field of a type, which heads its column and labels its row in the inspector:
 * the name of the attribute in the specification (`initialConcentration`, `fbc:charge`), and
 * plain words for what the report adds (`derived units`). The glossary is the only place where
 * an attribute is named, as it is the only place where it is explained; a field without an
 * entry, which the tests rule out, is named by its last segment. */
export function attributeLabel(type: SbmlType, field: string): string {
  return attributeEntry(type, field)?.label ?? field.slice(field.lastIndexOf(".") + 1);
}

export function linkEntry(kind: EdgeKind): GlossaryEntry | undefined {
  return glossary.links[kind];
}

/** The key of a link kind, `links/<kind>`, `undefined` where the kind has no entry. */
export function linkKey(kind: EdgeKind): string | undefined {
  return linkEntry(kind) ? `links/${kind}` : undefined;
}

/** The entry of a concept the report adds, by its key in `glossary/report.toml`. */
export function conceptEntry(key: string): GlossaryEntry | undefined {
  return glossary.concepts[key];
}

/** The label and the summary of any key the help dialog can open, from the eager glossary: the
 * header of the dialog while the long description and the technical detail of
 * `glossary-details.json` are still loading. A key of a type, an attribute, a link kind or a
 * concept resolves through the same lookup its own key helper uses; the eager glossary carries
 * no data types, so a `datatypes/...` key, and any key this cannot parse, is `undefined` and the
 * dialog falls back to the last segment of the key for its header. */
export function entryOfKey(key: string): GlossaryEntry | undefined {
  const slash = key.indexOf("/");
  if (slash === -1) return undefined;
  const namespace = key.slice(0, slash);
  const rest = key.slice(slash + 1);
  switch (namespace) {
    case "types": {
      const second = rest.indexOf("/");
      return second === -1
        ? typeEntry(rest as SbmlType)
        : attributeEntry(rest.slice(0, second) as SbmlType, rest.slice(second + 1));
    }
    case "links":
      return linkEntry(rest as EdgeKind);
    case "concepts":
      return conceptEntry(rest);
    default:
      return undefined;
  }
}
