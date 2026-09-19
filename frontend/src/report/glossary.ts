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

/** The first segment of a dotted field, e.g. "kineticLaw" of "kineticLaw.math". */
function firstSegment(field: string): string {
  const dot = field.indexOf(".");
  return dot === -1 ? field : field.slice(0, dot);
}

/** The entry of a field of a type: the exact field on the type, then the exact field on the
 * shared `SBase` attributes, then the first segment of a dotted field on the type, then the
 * first segment on `SBase`. */
export function attributeEntry(type: SbmlType, field: string): GlossaryEntry | undefined {
  const typeAttributes = glossary.types[type]?.attributes;
  const sbaseAttributes = glossary.types.SBase?.attributes;
  const exact = typeAttributes?.[field] ?? sbaseAttributes?.[field];
  if (exact) return exact;
  const segment = firstSegment(field);
  if (segment === field) return undefined;
  return typeAttributes?.[segment] ?? sbaseAttributes?.[segment];
}

export function linkEntry(kind: EdgeKind): GlossaryEntry | undefined {
  return glossary.links[kind];
}

/** The entry of a concept the report adds, by its key in `glossary/report.toml`. */
export function conceptEntry(key: string): GlossaryEntry | undefined {
  return glossary.concepts[key];
}

/** The url of the reference page of a type, which the inspector links from its header. */
export function referenceUrl(type: SbmlType): string {
  return `${DOCS_URL}${glossary.types[type]?.page ?? ""}`;
}
