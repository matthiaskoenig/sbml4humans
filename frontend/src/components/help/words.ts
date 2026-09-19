/** The fixed words of the help dialog are chrome of the interface and stand in the component
 * which shows them; everything which names or explains SBML or the report itself comes from the
 * glossary. This one word is shown by three of them - the badge of the header, the technical list
 * and the attributes table of a type all say of an attribute whether the specification requires
 * it - and so it stands once, here. */
export function requiredWord(required: boolean): string {
  return required ? "required" : "optional";
}
