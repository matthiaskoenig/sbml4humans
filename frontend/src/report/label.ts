import type { EdgeKind, SbmlType } from "@/api/types";
import type { ReportIndex } from "@/report/index";
import { pkKey } from "@/report/pk";

/** The three children of an event with the link kind which leads from the event to them. */
const EVENT_CHILD_KINDS: Partial<Record<SbmlType, EdgeKind>> = {
  Trigger: "trigger",
  Priority: "priority",
  Delay: "delay",
};

/** The name a link and the header of the inspector show for an element.
 *
 * It is the id of the element, and without one the key of its primary key, which is its meta id
 * or the name its parent gives it. Two kinds of element are named after the element they belong
 * to instead, because they carry an id in few models and a meta id says nothing about where they
 * sit: a species reference is named by its reaction and its species, which is what the inspector
 * of a species asks, and the trigger, the priority and the delay of an event are named by their
 * event and what they are. */
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
  const childKind = element?.sbmlType ? EVENT_CHILD_KINDS[element.sbmlType] : undefined;
  if (childKind) {
    const edge = index?.referencedBy(pk).find((e) => e.kind === childKind);
    const event = edge ? index?.get(edge.source)?.id : null;
    if (event) return `${event}.${childKind}`;
  }
  return pkKey(pk);
}
