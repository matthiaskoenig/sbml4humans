/** Whether a units latex is renderable: `UnitsView` and every composite that pairs an id link
 * with the id's units latex share this predicate, so a null, empty or "-" latex (the report's
 * placeholder for units which are not declared or cannot be derived, and the rendering of a units
 * attribute `dimensionless`, whose id says it already) never renders a KaTeX minus, and a link
 * paired with such a latex never shows a redundant placeholder next to it. */
export function hasUnitsLatex(latex: string | null | undefined): boolean {
  return latex !== null && latex !== undefined && latex !== "" && latex !== "-";
}
