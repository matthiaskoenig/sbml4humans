import type { EdgeKind, SbmlType } from "@/api/types";
import type { ReportIndex } from "@/report/index";
import { pkKey } from "@/report/pk";

/** The three children of an event with the link kind which leads from the event to them. */
const EVENT_CHILD_KINDS: Partial<Record<SbmlType, EdgeKind>> = {
  Trigger: "trigger",
  Priority: "priority",
  Delay: "delay",
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

/** The name a link and the header of the inspector show for an element.
 *
 * It is the id of the element, and without one the key of its primary key, which is its meta id
 * or the name its parent gives it. Two kinds of element are named after the element they belong
 * to instead, because they carry an id in few models and a meta id says nothing about where they
 * sit: a species reference is named by its reaction and its species, which is what the inspector
 * of a species asks, the trigger, the priority and the delay of an event are named by their
 * event and what they are, and a replacement of the comp package by the element it belongs to
 * and the submodel it reaches into. */
export function elementLabel(
  index: ReportIndex | null | undefined,
  pk: string | null | undefined,
): string | null {
  if (!pk) return null;
  const element = index?.get(pk);
  if (element?.id) return element.id;
  if (
    element &&
    (element.sbmlType === "SpeciesReference" || element.sbmlType === "ModifierSpeciesReference")
  ) {
    const participation = index?.participation(pk);
    const reaction = participation ? index?.get(participation.reaction)?.id : null;
    if (reaction) return `${reaction}.${element.species}`;
  }
  const replacementKind = element?.sbmlType ? REPLACEMENT_KINDS[element.sbmlType] : undefined;
  if (element && replacementKind && "submodelRef" in element) {
    const edge = index?.referencedBy(pk).find((e) => e.kind === replacementKind);
    const owner = edge ? index?.get(edge.source)?.id : null;
    if (owner) return `${owner}.${element.submodelRef}`;
  }
  // a leaf of a gene product association is named by the gene product it names, the way a link
  // of a comp reference chain is named by what it names
  if (element?.sbmlType === "GeneProductRef") return element.geneProduct;
  // a flux objective is named by the reaction it weighs, which is what its objective lists and
  // what its key would otherwise spell out behind the identifier of that objective
  if (element?.sbmlType === "FluxObjective") return element.reaction;
  // a link of a reference chain is named by what it names, which is what the file writes and
  // what its key would otherwise spell out as the key of its parent and the word sBaseRef
  if (element?.sbmlType === "SBaseRef") {
    const name = element.portRef ?? element.idRef ?? element.unitRef ?? element.metaIdRef;
    if (name) return name;
  }
  const childKind = element?.sbmlType ? EVENT_CHILD_KINDS[element.sbmlType] : undefined;
  if (childKind) {
    const edge = index?.referencedBy(pk).find((e) => e.kind === childKind);
    const event = edge ? index?.get(edge.source)?.id : null;
    if (event) return `${event}.${childKind}`;
  }
  const influenceKind = element?.sbmlType ? INFLUENCE_KINDS[element.sbmlType] : undefined;
  if (element && influenceKind && "qualitativeSpecies" in element) {
    const edge = index?.referencedBy(pk).find((e) => e.kind === influenceKind);
    const transition = edge ? index?.get(edge.source)?.id : null;
    if (transition) return `${transition}.${element.qualitativeSpecies}`;
  }
  return pkKey(pk);
}
