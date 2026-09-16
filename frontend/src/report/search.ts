import type { Math, SBase } from "@/api/types";

const texts = new WeakMap<SBase, string>();

export function normalizeQuery(query: string): string {
  return query.trim().toLowerCase();
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, " ");
}

function* maths(element: SBase): Generator<Math | null | undefined> {
  if ("math" in element) yield element.math;
  if (element.sbmlType === "Reaction") yield element.kineticLaw?.math;
  if (element.sbmlType === "Event") {
    yield element.trigger?.math;
    yield element.priority;
    yield element.delay;
    for (const assignment of element.listOfEventAssignments ?? []) yield assignment.math;
  }
  if (element.sbmlType === "Uncertainty") {
    for (const parameter of element.uncertParameters ?? []) yield parameter.math;
  }
}

/** The searchable text of an element: id, name, metaId, sbo, notes text, formulas and equation. */
function searchText(element: SBase): string {
  const cached = texts.get(element);
  if (cached !== undefined) return cached;
  const parts: (string | null | undefined)[] = [
    element.id,
    element.name,
    element.metaId,
    element.sbo,
  ];
  if (element.notes) parts.push(stripHtml(element.notes));
  for (const math of maths(element)) parts.push(math?.formula);
  if (element.sbmlType === "Reaction") parts.push(element.equation);
  const text = parts
    .filter((part): part is string => !!part)
    .join("\n")
    .toLowerCase();
  texts.set(element, text);
  return text;
}

/** Case insensitive substring match of the query against the searchable text. */
export function matches(element: SBase, query: string): boolean {
  const normalized = normalizeQuery(query);
  return normalized === "" || searchText(element).includes(normalized);
}
