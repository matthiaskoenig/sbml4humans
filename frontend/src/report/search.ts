import type {
  Math,
  ReplacedBy,
  ReplacedElement,
  SBase,
  SBaseRef,
  UncertMeasure,
  Uncertainty,
} from "@/api/types";
import type { ReportIndex } from "@/report/index";

/** The searchable text of every element, per index: the text of a rule holds the name of the
 * element it sets, which only the index of its report knows. */
const texts = new WeakMap<object, WeakMap<SBase, string>>();
/** The key of the texts built without an index. */
const NO_INDEX = {};

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

/** The elements a file nests in a row of a table, which are part of that row and no row of their
 * own: the species references and the local parameters of a reaction, the trigger, the priority,
 * the delay and the assignments of an event, the inputs, the outputs and the terms of a
 * transition, the deletions of a submodel, the terms of an objective and of a user defined
 * constraint. */
function* nested(element: SBase): Generator<SBase | null | undefined> {
  switch (element.sbmlType) {
    case "Reaction":
      yield* element.listOfReactants ?? [];
      yield* element.listOfProducts ?? [];
      yield* element.listOfModifiers ?? [];
      yield element.kineticLaw;
      yield* element.kineticLaw?.listOfLocalParameters ?? [];
      break;
    case "Event":
      yield element.trigger;
      yield element.priority;
      yield element.delay;
      yield* element.listOfEventAssignments ?? [];
      break;
    case "Transition":
      yield* element.listOfInputs ?? [];
      yield* element.listOfOutputs ?? [];
      yield* element.listOfFunctionTerms ?? [];
      yield element.defaultTerm;
      break;
    case "Submodel":
      yield* element.listOfDeletions ?? [];
      break;
    case "Objective":
      yield* element.listOfFluxObjectives ?? [];
      break;
    case "UserDefinedConstraint":
      yield* element.listOfUserDefinedConstraintComponents ?? [];
      break;
    default:
      break;
  }
}

/** What a reference of the comp package names, down its chain of references: the port, the id,
 * the unit, the meta id or the deletion inside a submodel, which a reader looks for an element
 * by when a submodel offers it through a port. */
function* referenceNames(
  reference:
    (SBaseRef & { deletion?: string | null }) | ReplacedBy | ReplacedElement | null | undefined,
): Generator<string | null | undefined> {
  if (!reference) return;
  yield reference.portRef;
  yield reference.idRef;
  yield reference.unitRef;
  yield reference.metaIdRef;
  if ("deletion" in reference) yield reference.deletion;
  yield* referenceNames(reference.sbaseRef);
}

/** The name of the element an initial assignment, a rule or an event assignment sets, which
 * is what a reader looks for it by when it carries no id of its own. */
function targetName(element: SBase, index: ReportIndex | undefined): string | null | undefined {
  if (!index) return null;
  const symbol = "symbol" in element ? element.symbol : null;
  const variable =
    "variable" in element && typeof element.variable === "string" ? element.variable : null;
  const target = symbol
    ? index.resolve(element.pk, "symbol", symbol)
    : variable
      ? index.resolve(element.pk, "variable", variable)
      : null;
  return target ? index.get(target)?.name : null;
}

/** The searchable text of an element: id, name, metaId, sbo, the element it sets and its name,
 * notes text, formulas, equation, the uncertainties it carries, the ids and the names of the
 * elements nested in it, what its replacements name inside a submodel and the label of a gene
 * product. An initial assignment, a rule and an event assignment carry no id in most models, and
 * a reader looks for them by the symbol or the variable they set. */
function searchText(element: SBase, index: ReportIndex | undefined): string {
  let cache = texts.get(index ?? NO_INDEX);
  if (!cache) {
    cache = new WeakMap();
    texts.set(index ?? NO_INDEX, cache);
  }
  const cached = cache.get(element);
  if (cached !== undefined) return cached;
  const parts: (string | null | undefined)[] = [
    element.id,
    element.name,
    element.metaId,
    element.sbo,
  ];
  if ("symbol" in element) parts.push(element.symbol);
  if ("variable" in element) parts.push(element.variable);
  parts.push(targetName(element, index));
  if (element.sbmlType === "GeneProduct") parts.push(element.label);
  for (const child of nested(element)) {
    parts.push(child?.id, child?.name);
    if (child && "variable" in child && typeof child.variable === "string") {
      parts.push(child.variable, targetName(child, index));
    }
  }
  if (element.comp?.replacedBy) parts.push(...referenceNames(element.comp.replacedBy));
  for (const replaced of element.comp?.replacedElements ?? []) {
    parts.push(...referenceNames(replaced));
  }
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
  cache.set(element, text);
  return text;
}

/** Case insensitive substring match of the query against the searchable text, which with the
 * index of the report holds the names of the elements a rule or an assignment sets. */
export function matches(element: SBase, query: string, index?: ReportIndex): boolean {
  const normalized = normalizeQuery(query);
  return normalized === "" || searchText(element, index).includes(normalized);
}
