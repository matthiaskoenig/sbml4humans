/** The report writes the reaction equation with numeric character references (`&#10142;`
 * for the arrow), which read as markup in a text cell. */
export function decodeReferences(text: string): string {
  return text.replace(/&#(\d+);/g, (_, code: string) => String.fromCodePoint(Number(code)));
}

/** Whether the text is safe to bind as an anchor `href`: the report passes values such as a
 * definition url or an annotation resource through verbatim, so only `http(s)` is ever rendered
 * as a link, never a `javascript:` or other scheme. */
export function isHttpUrl(text: string | null | undefined): boolean {
  return text !== null && text !== undefined && /^https?:\/\//.test(text);
}
