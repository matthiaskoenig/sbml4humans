/** Whether the text is safe to bind as an anchor `href`: the report passes values such as a
 * definition url or an annotation resource through verbatim, so only `http(s)` is ever rendered
 * as a link, never a `javascript:` or other scheme. The text is trimmed and the scheme matched
 * case insensitively, the way a browser reads it. */
export function isHttpUrl(text: string | null | undefined): boolean {
  return text !== null && text !== undefined && /^https?:\/\//i.test(text.trim());
}

/** The name a definition url is shown by: its last segment, behind the last `/` and the last
 * `#`, which is the local name of the term it names (`.../Beta_distribution#alpha` reads as
 * `alpha`). A url which ends in a separator keeps the segment before it, and a url without one
 * is shown whole. The full url is the tooltip of the link. */
export function definitionLabel(url: string): string {
  const segments = url.split(/[/#]/).filter((segment) => segment !== "");
  return segments[segments.length - 1] ?? url;
}

/** The most characters a column of a nested table is given: a longer text wraps, the name the
 * report gives an element at a dot, so that a table of a genome scale model, whose names run
 * over thirty characters, does not push its other columns out of the pane. */
export const MAX_COLUMN_CHARS = 18;

/** The characters of the monospace font a column of a nested table needs: its longest text or
 * its header, whichever is longer, up to MAX_COLUMN_CHARS. A header, which is set in the
 * proportional font, is counted as if it were monospace, which leaves it room. The tables of one
 * element which stand under each other take the widths of their columns from all of their rows
 * together, so that a column lines up with the same column of the table above it. */
export function columnChars(header: string, texts: Iterable<string | null | undefined>): number {
  let chars = header.length;
  for (const text of texts) chars = Math.max(chars, text?.length ?? 1);
  return Math.min(chars, Math.max(header.length, MAX_COLUMN_CHARS));
}

/** The file name of a manifest location, `omex_minimal.xml` of `./models/omex_minimal.xml`:
 * what a link into another entry shows of it, where the whole location would not fit. */
export function fileName(location: string): string {
  const name = location.slice(location.lastIndexOf("/") + 1);
  return name || location;
}
