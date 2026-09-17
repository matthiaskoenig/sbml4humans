import rawGlossary from "@/data/glossary.json";

import type { EdgeKind, SbmlType } from "@/api/types";

export interface GlossaryEntry {
  label: string;
  summary: string;
}

/** A type entry of the glossary: the shared `SBase` entry and the four package entries
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
 * Vitest does not load `.env.development`, so this falls back to the site's own default. */
export const DOCS_URL: string =
  (import.meta.env.VITE_DOCS_URL as string | undefined) ??
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

/** The anchor of an attribute label: lower case, every run of non alphanumeric characters
 * collapsed to a single dash. */
function anchorOf(label: string): string {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/** The url of the reference page of a type, or of one of its attributes when `field` is given. */
export function referenceUrl(type: SbmlType, field?: string): string {
  const base = `${DOCS_URL}${glossary.types[type]?.page ?? ""}`;
  if (!field) return base;
  const label = attributeEntry(type, field)?.label;
  return label ? `${base}#${anchorOf(label)}` : base;
}
