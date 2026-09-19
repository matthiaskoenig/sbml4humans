import type { Deletion, EdgeKind, Port, ReplacedBy, ReplacedElement, SBaseRef } from "@/api/types";
import type { ReportIndex } from "@/report/index";

/** The comp objects which name an element of a model: a port, a deletion, a replacement and a
 * link of a reference chain (comp §3.7). */
export type CompReference = Port | Deletion | ReplacedElement | ReplacedBy | SBaseRef;

/** The name a comp reference gives the element it names, in the order of the specification: the
 * port first, then the identifier, the unit identifier and the meta id. Exactly one of them is
 * set, and a replacement which is scoped to a deletion sets none. */
export function referenceName(ref: CompReference): string | null {
  return ref.portRef ?? ref.idRef ?? ref.unitRef ?? ref.metaIdRef ?? null;
}

/** The element a comp reference ends at, read from the edge the report resolved it to.
 *
 * A replacement carries two edges of its kind, one to the submodel it names and one to the
 * element inside it; where the reference could not be resolved, because the model of the
 * submodel is an external one the report does not read, the only edge is the one to the
 * submodel and the reference ends nowhere. */
export function referenceTarget(
  index: ReportIndex | null | undefined,
  pk: string,
  kind: EdgeKind,
  submodel: string | null = null,
): string | null {
  const edge = index?.references(pk).find((e) => e.kind === kind && e.target !== submodel);
  return edge?.target ?? null;
}
