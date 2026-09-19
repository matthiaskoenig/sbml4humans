import type { Math, SBase, UncertMeasure, Uncertainty } from "@/api/types";

const texts = new WeakMap<SBase, string>();

export function normalizeQuery(query: string): string {
  return query.trim().toLowerCase();
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, " ");
}

/** The math of every measure of an uncertainty, of the ones nested in a distribution as
 * well (distrib §3.11.7). */
function* measureMaths(measures: UncertMeasure[]): Generator<Math | null | undefined> {
  for (const measure of measures) {
    yield measure.math;
    yield* measureMaths(measure.uncertParameters ?? []);
  }
}

function* maths(element: SBase): Generator<Math | null | undefined> {
  if ("math" in element) yield element.math;
  if (element.sbmlType === "Reaction") yield element.kineticLaw?.math;
  if (element.sbmlType === "Event") {
    yield element.trigger?.math;
    yield element.priority?.math;
    yield element.delay?.math;
    for (const assignment of element.listOfEventAssignments ?? []) yield assignment.math;
  }
  if (element.sbmlType === "Uncertainty") {
    yield* measureMaths(element.uncertParameters ?? []);
  }
  if (element.sbmlType === "Transition") {
    for (const term of element.listOfFunctionTerms ?? []) yield term.math;
  }
}

/** The text of an uncertainty and of every measure below it: the id, the name, the notes and
 * the type of a measure. An uncertainty is no row of a table but part of the inspector of the
 * element whose value it describes, so that element is what the search finds. */
function* uncertaintyTexts(
  owners: (Uncertainty | UncertMeasure)[],
): Generator<string | null | undefined> {
  for (const owner of owners) {
    yield owner.id;
    yield owner.name;
    if (owner.notes) yield stripHtml(owner.notes);
    if ("type" in owner) yield owner.type;
    yield* uncertaintyTexts(owner.uncertParameters ?? []);
  }
}

/** The searchable text of an element: id, name, metaId, sbo, the element it sets, notes text,
 * formulas, equation and the uncertainties it carries. An initial assignment, a rule and an
 * event assignment carry no id in most models, and a reader looks for them by the symbol or the
 * variable they set. */
function searchText(element: SBase): string {
  const cached = texts.get(element);
  if (cached !== undefined) return cached;
  const parts: (string | null | undefined)[] = [
    element.id,
    element.name,
    element.metaId,
    element.sbo,
  ];
  if ("symbol" in element) parts.push(element.symbol);
  if ("variable" in element) parts.push(element.variable);
  if (element.notes) parts.push(stripHtml(element.notes));
  // the message of a constraint is XHTML written for a reader, like the notes, and a reader
  // looks for a constraint by what its message says
  if (element.sbmlType === "Constraint" && element.message) parts.push(stripHtml(element.message));
  for (const math of maths(element)) parts.push(math?.formula);
  if (element.sbmlType === "Reaction") parts.push(element.equation);
  // the math of the measures is among the formulas of an uncertainty, which is part of the
  // element in the same way
  for (const uncertainty of element.uncertainties ?? []) {
    parts.push(...uncertaintyTexts([uncertainty]));
    for (const math of maths(uncertainty)) parts.push(math?.formula);
  }
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
