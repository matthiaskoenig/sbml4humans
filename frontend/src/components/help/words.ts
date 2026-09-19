/** The fixed words of the help dialog are chrome of the interface and stand in the component
 * which shows them; these two are shown by more than one of them and so stand once, here. */

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
