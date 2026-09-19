import type { EdgeKind, SbmlType } from "@/api/types";
import type { ReportIndex } from "@/report/index";
import { pkKey } from "@/report/pk";

/** The elements a file nests in another one which are named after that element and their place
 * in it, with the link kind which leads from that element to them: the kinetic law of a
 * reaction, the trigger, the priority and the delay of an event, and the default term of a
 * transition. A reaction has one kinetic law and an event one of each of the three, so the place
 * says which one it is. */
const PLACE_KINDS: Partial<Record<SbmlType, EdgeKind>> = {
  KineticLaw: "kineticLaw",
  Trigger: "trigger",
  Priority: "priority",
  Delay: "delay",
  DefaultTerm: "defaultTerm",
};

/** The two replacements of the comp package with the link kind which leads from the element
 * they belong to to them. */
const REPLACEMENT_KINDS: Partial<Record<SbmlType, EdgeKind>> = {
  ReplacedElement: "replacedElement",
  ReplacedBy: "replacedBy",
};

/** The two influences of a transition with the link kind which leads from the transition to
 * them. An input and an output carry an identifier in few models, so they are named after
 * their transition and the species they name, the way a species reference is named after its
 * reaction and its species. */
const INFLUENCE_KINDS: Partial<Record<SbmlType, EdgeKind>> = {
  Input: "input",
  Output: "output",
};

/** The tooltip of a name the report gives an element the file gives no id: it is set in
 * italics wherever it stands, so that it is told apart from an id the file writes. */
export const REPORT_NAME_HINT = "no id in the file: the name the report gives the element";

/** Whether the element carries an id of the file, which is the name a link shows of it. An
 * element without one is shown by the name the report gives it, and that name is marked. */
export function hasFileId(
  index: ReportIndex | null | undefined,
  pk: string | null | undefined,
): boolean {
  return !!(pk && index?.get(pk)?.id);
}

/** How many elements the name of an element follows outwards. A file nests an element three
 * deep at most, a replacement of a species reference of a reaction, so the limit only keeps a
 * graph which is not a tree from recursing without end. */
const MAX_DEPTH = 8;

/** The name a link and the header of the inspector show for an element.
 *
 * It is the id of the element, and without one the key of its primary key, which is its meta id
 * or the name its parent gives it. An element which the file nests in another one is named after
 * that element instead, because it carries an id in few models and a meta id says nothing about
 * where it sits: a species reference by its reaction and its species, which is what the inspector
 * of a species asks, the kinetic law of a reaction and the trigger, the priority and the delay of
 * an event by their owner and what they are, an event assignment by its event and the element it
 * sets, a term of a transition by its transition and its place in the table, a replacement of
 * the comp package by the element it belongs to and the submodel it reaches into, a reference of
 * a gene product association by its reaction and its gene product, and a flux objective by its
 * objective and its reactions. The owner is named by the same rule, so an event without an id
 * lends its key to its trigger. */
export function elementLabel(
  index: ReportIndex | null | undefined,
  pk: string | null | undefined,
): string | null {
  return label(index, pk, 0);
}

/** The name of an element whose owners have been followed `depth` elements outwards. */
function label(
  index: ReportIndex | null | undefined,
  pk: string | null | undefined,
  depth: number,
): string | null {
  if (!pk) return null;
  const element = index?.get(pk);
  if (element?.id) return element.id;
  if (!index || !element || depth > MAX_DEPTH) return pkKey(pk);

  /** The element which names this one through a link of the kind, and the name it has. */
  const owner = (kind: EdgeKind): { pk: string; name: string | null } | null => {
    const source = index.referencedBy(pk).find((edge) => edge.kind === kind)?.source;
    return source ? { pk: source, name: label(index, source, depth + 1) } : null;
  };

  if (element.sbmlType === "SpeciesReference" || element.sbmlType === "ModifierSpeciesReference") {
    const reaction = index.participation(pk)?.reaction;
    const name = reaction ? label(index, reaction, depth + 1) : null;
    if (name) return `${name}.${element.species}`;
  }
  const placeKind = element.sbmlType ? PLACE_KINDS[element.sbmlType] : undefined;
  if (placeKind) {
    const name = owner(placeKind)?.name;
    if (name) return `${name}.${placeKind}`;
  }
  if (element.sbmlType === "EventAssignment") {
    const name = owner("eventAssignment")?.name;
    if (name) return `${name}.${element.variable}`;
  }
  if (element.sbmlType === "FunctionTerm") {
    const transition = owner("functionTerm");
    const terms = transition ? index.get(transition.pk) : undefined;
    if (transition?.name && terms?.sbmlType === "Transition") {
      const place = (terms.listOfFunctionTerms ?? []).findIndex((term) => term.pk === pk);
      if (place !== -1) return `${transition.name}.functionTerm.${place}`;
    }
  }
  const replacementKind = element.sbmlType ? REPLACEMENT_KINDS[element.sbmlType] : undefined;
  if (replacementKind && "submodelRef" in element) {
    const name = owner(replacementKind)?.name;
    if (name) return `${name}.${element.submodelRef}`;
  }
  // a leaf of a gene product association is named after the reaction whose tree holds it and
  // the gene product it names, the way a species reference is named after its reaction and its
  // species: named by its gene alone, it read as the gene product itself
  if (element.sbmlType === "GeneProductRef") {
    const reaction = index.associationReaction(pk);
    const name = reaction ? label(index, reaction, depth + 1) : null;
    if (name) return `${name}.${element.geneProduct}`;
  }
  // a flux objective is named after its objective and the reactions whose fluxes it multiplies,
  // one for a linear term and two for a product: named by its reaction alone, it read as the
  // reaction it weighs
  if (element.sbmlType === "FluxObjective") {
    const name = owner("fluxObjective")?.name;
    const reactions = [element.reaction, element.reaction2].filter((id) => !!id).join(".");
    if (name && reactions) return `${name}.${reactions}`;
  }
  // a link of a reference chain is named by what it names, which is what the file writes and
  // what its key would otherwise spell out as the key of its parent and the word sBaseRef
  if (element.sbmlType === "SBaseRef") {
    const name = element.portRef ?? element.idRef ?? element.unitRef ?? element.metaIdRef;
    if (name) return name;
  }
  const influenceKind = element.sbmlType ? INFLUENCE_KINDS[element.sbmlType] : undefined;
  if (influenceKind && "qualitativeSpecies" in element) {
    const name = owner(influenceKind)?.name;
    if (name) return `${name}.${element.qualitativeSpecies}`;
  }
  return pkKey(pk);
}
