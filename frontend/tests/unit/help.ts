/** The key of the entry a help link opens. Every one of them is a real anchor whose href is the
 * route of the report with `help=<key>`, which is what the dialog reads, so the href is where a
 * test asks which entry a label, a column header or a heading explains. */
export function helpKeyOf(href: string | undefined): string | null {
  return new URL(href ?? "", "http://localhost").searchParams.get("help");
}

/** The accessible name of an element, as a screen reader would compute it: `aria-label` where the
 * element carries one, else the concatenation of the accessible names of its children, recursing
 * into text and elements alike. It is the small part of the accname algorithm the report needs to
 * test that a heading which contains an icon link is not also named by that link's own label. */
export function accessibleName(element: Element): string {
  const label = element.getAttribute("aria-label");
  if (label !== null) return label.trim();
  let name = "";
  for (const child of Array.from(element.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) name += child.textContent ?? "";
    else if (child.nodeType === Node.ELEMENT_NODE) name += ` ${accessibleName(child as Element)}`;
  }
  return name.replace(/\s+/g, " ").trim();
}
