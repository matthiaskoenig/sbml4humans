import katex from "katex";

/** A latex longer than this many characters is not rendered: at tens of thousands of characters
 * KaTeX takes seconds and produces megabytes of html for a single formula, synchronously, in
 * every row that renders it. */
export const MAX_LATEX_LENGTH = 10_000;

/** KaTeX has no metrics for the micro sign of the report and warns about it. */
function normalize(latex: string): string {
  return latex.replaceAll("µ", "\\mu ");
}

/**
 * Renders a latex formula with KaTeX for use with `v-html`, or returns null when it should not
 * be rendered: when it is longer than `MAX_LATEX_LENGTH` and `unlimited` is not set, or when
 * KaTeX throws, for example on deeply nested braces (`throwOnError: false` only covers errors
 * KaTeX raises itself, not a `RangeError` from the parser's recursion).
 */
export function renderLatex(
  latex: string,
  options: { display?: boolean; unlimited?: boolean } = {},
): string | null {
  const normalized = normalize(latex);
  // the cap applies to the normalised latex: the micro sign expands to "\mu " (four characters
  // for one), so checking the raw latex would let a formula reach KaTeX at close to four times
  // MAX_LATEX_LENGTH.
  if (!options.unlimited && normalized.length > MAX_LATEX_LENGTH) return null;
  try {
    return katex.renderToString(normalized, {
      throwOnError: false,
      strict: "ignore",
      output: "html",
      trust: false,
      maxSize: 10,
      maxExpand: 1000,
      displayMode: options.display ?? false,
    });
  } catch {
    return null;
  }
}
