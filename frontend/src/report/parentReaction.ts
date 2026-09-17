import type { Reaction } from "@/api/types";
import type { ReportIndex } from "@/report/index";

export type ParentReactionKind = "reactant" | "product" | "modifier";

/** The reaction listing a species or modifier reference and the role of the reference in it,
 * found by scanning the reactions of the element's model. Shared by `SpeciesReferenceAttributes`
 * and `ModifierSpeciesReferenceAttributes`. */
export function parentReaction(
  index: ReportIndex | null,
  pk: string,
): { reaction: Reaction; kind: ParentReactionKind } | null {
  const modelId = index?.modelOf(pk);
  if (!index || !modelId) return null;
  const reactions = (index.byType(modelId).get("Reaction") ?? []).filter(
    (element): element is Reaction => element.sbmlType === "Reaction",
  );
  for (const reaction of reactions) {
    if (reaction.listOfReactants?.some((r) => r.pk === pk)) return { reaction, kind: "reactant" };
    if (reaction.listOfProducts?.some((r) => r.pk === pk)) return { reaction, kind: "product" };
    if (reaction.listOfModifiers?.some((r) => r.pk === pk)) return { reaction, kind: "modifier" };
  }
  return null;
}
