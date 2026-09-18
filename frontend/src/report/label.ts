import type { ReportIndex } from "@/report/index";
import { pkKey } from "@/report/pk";

/** The name a link and the header of the inspector show for an element.
 *
 * It is the id of the element, and without one the key of its primary key, which is its meta id
 * or the name its parent gives it. A species reference is named by its reaction and its species
 * instead: it carries an id in few models, and neither a meta id nor a key tells a reader which
 * participation of which reaction it is, which is what the inspector of a species asks. */
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
  return pkKey(pk);
}
