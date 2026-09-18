import type { Association } from "@/api/types";

/** The nodes one `and` or `or` of the inspector shows before a "show all" button. It is far
 * below the limit of a flat list, because every node of an association opens a group of its
 * own: an `or` of a thousand complexes would otherwise be a wall of links. */
export const ASSOCIATION_LIMIT = 5;

/** The operator levels the inspector renders before a group becomes a button which opens it.
 * Two levels are the shape of almost every association, `(a and b) or (c and d)`, and they
 * bound the links of one attribute row at the limit of a group squared. */
export const ASSOCIATION_DEPTH = 1;

/** The genes a table cell writes out before it ends the expression with an ellipsis. One
 * reaction of Recon3D names five thousand gene products in one `or`, and the cell of a table
 * is one line. */
export const GENE_TEXT_LIMIT = 10;

/** The association as the expression it stands for: `(b3916 or b1723)`.
 *
 * It is the text of the table cell, where the tree cannot be rendered as the nested links the
 * inspector shows. The walk stops after `limit` gene products and closes the expression with an
 * ellipsis, so that the cost of a cell does not grow with the size of the association. */
export function geneAssociationText(
  node: Association | null | undefined,
  limit: number = GENE_TEXT_LIMIT,
): string {
  if (!node) return "";
  let genes = 0;

  function walk(current: Association): string {
    if (current.sbmlType === "GeneProductRef") {
      genes += 1;
      return current.geneProduct ?? "";
    }
    const operator = current.sbmlType === "And" ? " and " : " or ";
    const parts: string[] = [];
    for (const child of "associations" in current ? (current.associations ?? []) : []) {
      if (genes >= limit) {
        parts.push("…");
        break;
      }
      parts.push(walk(child));
    }
    return `(${parts.join(operator)})`;
  }

  return walk(node);
}
