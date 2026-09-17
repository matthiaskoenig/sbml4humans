/** Whether the text is safe to bind as an anchor `href`: the report passes values such as a
 * definition url or an annotation resource through verbatim, so only `http(s)` is ever rendered
 * as a link, never a `javascript:` or other scheme. The text is trimmed and the scheme matched
 * case insensitively, the way a browser reads it. */
export function isHttpUrl(text: string | null | undefined): boolean {
  return text !== null && text !== undefined && /^https?:\/\//i.test(text.trim());
}
