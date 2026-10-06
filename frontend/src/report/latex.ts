import katex from "katex";
import "katex/dist/katex.min.css";

import "@/assets/latex.css";

/** A latex longer than this many characters is not rendered: at tens of thousands of characters
 * KaTeX takes seconds and produces megabytes of html for a single formula, synchronously, in
 * every row that renders it. */
export const MAX_LATEX_LENGTH = 10_000;

/** KaTeX has no metrics for the micro sign of the report and warns about it. */
function normalize(latex: string): string {
  return latex.replaceAll("µ", "\\mu ");
}

/** The one command KaTeX may trust, for a formula with links: `\htmlData{pk=<pk>}{<symbol>}`
 * of the differential equations, which the backend writes around a symbol of an element and
 * which KaTeX renders as an element with `data-pk`. Every other command which writes html or a
 * link (`\href`, `\url`, `\htmlClass`, `\htmlId`, `\htmlStyle`), and `\htmlData` with any
 * attribute but `pk`, stays untrusted and renders as its text. */
function trustLink(context: { command: string; attributes?: Record<string, string> }): boolean {
  if (context.command !== "\\htmlData") return false;
  // KaTeX names the attributes of `\htmlData` as they are written, `data-pk`
  const keys = Object.keys(context.attributes ?? {});
  return keys.length === 1 && keys[0] === "data-pk";
}

/**
 * Renders a latex formula with KaTeX for use with `v-html`, or returns null when it should not
 * be rendered: when it is longer than `MAX_LATEX_LENGTH` and `unlimited` is not set, or when
 * KaTeX throws, for example on deeply nested braces (`throwOnError: false` only covers errors
 * KaTeX raises itself, not a `RangeError` from the parser's recursion). `links` renders the
 * `\htmlData{pk=...}` of the symbols of an equation as elements with `data-pk`, see `trustLink`.
 */
export function renderLatex(
  latex: string,
  options: { display?: boolean; unlimited?: boolean; links?: boolean } = {},
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
      trust: options.links ? trustLink : false,
      maxSize: 10,
      maxExpand: 1000,
      displayMode: options.display ?? false,
    });
  } catch {
    return null;
  }
}
