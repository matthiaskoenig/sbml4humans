/** The report writes the reaction equation with numeric character references (`&#10142;`
 * for the arrow), which read as markup in a text cell. */
export function decodeReferences(text: string): string {
  return text.replace(/&#(\d+);/g, (_, code: string) => String.fromCodePoint(Number(code)));
}
