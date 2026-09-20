import type { GlossaryDetails, HelpEntry } from "@/report/glossaryDetails";

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

/** A few entries in the shape the generator writes, enough for every part of the dialog: a type
 * with attributes, rules and related entries, one of its attributes, the common attributes the
 * last row of an attributes table leads to, a data type and a link kind, which carries nothing
 * but its description. */
export const ENTRIES: Record<string, HelpEntry> = {
  "types/Species": {
    kind: "type",
    label: "Species",
    summary: "a pool of a chemical entity in a compartment",
    description: "A species is located in a [compartment](glossary:types/Compartment).",
    package: "core",
    docs: "reference/species/",
    spec: { label: "core 4.6", section: "4.6", url: "https://example.invalid/core" },
    rules: [
      {
        id: 20623,
        severity: "error",
        message: "A <species> object must have the required attributes 'id' and 'compartment'.",
        section: "L3V2 Section 4.6",
      },
      {
        id: 10713,
        severity: "warning",
        message: "The value of 'sboTerm' is expected to be an SBO identifier.",
      },
    ],
    attributes: ["types/Species/initialAmount"],
    related: ["types/Compartment"],
  },
  "types/Species/initialAmount": {
    kind: "attribute",
    label: "initialAmount",
    summary: "the amount of the species when the simulation starts",
    description: "The initial amount is the quantity of the species at the start of a simulation.",
    package: "core",
    docs: "reference/species/#initialamount",
    owner: "types/Species",
    type: { label: "double", key: "datatypes/double" },
    spec: { label: "core 4.6.4", section: "4.6.4", url: "https://example.invalid/core" },
    required: false,
    default: "the quantity is unknown or set by an initial assignment or a rule",
    rules: [{ id: 20609, severity: "error", message: "A <species> cannot set both values." }],
  },
  "types/Compartment": {
    kind: "type",
    label: "Compartment",
    summary: "a bounded space in which species are located",
    description: "A compartment is a bounded space.",
    package: "core",
    docs: "reference/compartment/",
  },
  "types/SBase": {
    kind: "type",
    label: "SBase",
    summary: "the attributes every element of an SBML model carries",
    description: "Almost every object of an SBML model derives from `SBase`.",
    package: "core",
    docs: "reference/sbase/",
    attributes: ["types/SBase/id"],
  },
  "types/SBase/id": {
    kind: "attribute",
    label: "id",
    summary: "the identifier other elements of the model use to reference the element",
    description: "The id is the name of the element inside the model.",
    package: "core",
    docs: "reference/sbase/#id",
    owner: "types/SBase",
    type: { label: "SId", key: "datatypes/SId" },
    required: false,
  },
  "datatypes/double": {
    kind: "datatype",
    label: "double",
    summary: "a number with a fractional part and an exponent",
    description: "A double is a floating point number.",
    package: "core",
    docs: "reference/datatypes/#double",
    values: ["1.0", "2.0"],
  },
  "datatypes/SId": {
    kind: "datatype",
    label: "SId",
    summary: "an identifier of an element of a model",
    description: "An SId is an identifier.",
    package: "core",
    docs: "reference/datatypes/#sid",
  },
  "links/compartment": {
    kind: "link",
    label: "compartment",
    summary: "the compartment a species is located in",
    description: "Every [species](glossary:types/Species) names its compartment.",
    package: "core",
    docs: "reference/links/#compartment",
  },
};

export const DETAILS: GlossaryDetails = { entries: ENTRIES };

/** jsdom implements the `<dialog>` element and its `open` attribute and nothing else: neither
 * `showModal` nor `close` exists on `HTMLDialogElement`. These give it the part of the behaviour
 * the dialog builds on, a modal which opens, closes and fires `close` as Escape does. */
export function stubDialogElement(): void {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement): void {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement): void {
    if (!this.hasAttribute("open")) return;
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
}
