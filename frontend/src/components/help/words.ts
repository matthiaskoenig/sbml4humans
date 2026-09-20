/** The fixed words of the help dialog are chrome of the interface and stand in the component
 * which shows them; these are shown by more than one of them and so stand once, here. */

/** The name of a help link which shows its icon alone, `HelpButton`: it stands next to a control
 * which already carries the label of the entry, the sort button of a column and the heading of a
 * section, so the label alone would name two things of the same page alike. `explain` is a word
 * of the chrome, the label is the one the glossary gives the entry. */
export function explainName(label: string): string {
  return `explain ${label}`;
}

/** Whether the specification requires an attribute, where the word stands on its own: the badge
 * of the header and the column of the attributes table of a type. */
export function requiredWord(required: boolean): string {
  return required ? "required" : "optional";
}

/** The same, as the answer of the row of the technical list, whose label already asks it:
 * "required: optional" reads as a contradiction, "required: no" as the answer it is. */
export function requiredAnswer(required: boolean): string {
  return required ? "yes" : "no";
}
