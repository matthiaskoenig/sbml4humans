import type { HighlighterCore, LanguageRegistration } from "shiki/core";

import type { OdeFormat } from "@/api/client";

/** The length above which a code is shown plain, in characters: highlighting it would block the
 * page for seconds. */
export const HIGHLIGHT_LIMIT = 200_000;

/** The grammar of Shiki of each format of sbmlode. */
const LANGUAGES: Record<OdeFormat, string> = {
  python: "python",
  julia: "julia",
  r: "r",
  latex: "latex",
  typst: "typst",
  markdown: "markdown",
};

const THEME = "github-light";

let highlighter: Promise<HighlighterCore> | null = null;

/** A grammar of `tm-grammars` (the grammars of Shiki as plain JSON) as a language of Shiki. The
 * languages of Shiki itself import every language they embed, a julia string of C++ or a raw block
 * of typst in any language, which would load megabytes the code of sbmlode never uses: the
 * grammars are loaded alone, an embedded block is not highlighted. */
async function grammar(json: Promise<{ default: object }>): Promise<LanguageRegistration> {
  return { ...((await json).default as LanguageRegistration), embeddedLangs: [] };
}

/** The highlighter of the six formats, created with the first code shown: Shiki, its grammars and
 * its theme are chunks of their own which only the code of the equations loads. The regular
 * expressions run on the JavaScript engine, so no WebAssembly is loaded. LaTeX builds on the
 * grammar of TeX, which is loaded with it. */
function load(): Promise<HighlighterCore> {
  highlighter ??= (async () => {
    const [{ createHighlighterCore }, { createJavaScriptRegexEngine }] = await Promise.all([
      import("shiki/core"),
      import("shiki/engine/javascript"),
    ]);
    return createHighlighterCore({
      themes: [import("shiki/themes/github-light.mjs")],
      langs: await Promise.all([
        grammar(import("tm-grammars/grammars/python.json")),
        grammar(import("tm-grammars/grammars/julia.json")),
        grammar(import("tm-grammars/grammars/r.json")),
        grammar(import("tm-grammars/grammars/tex.json")),
        grammar(import("tm-grammars/grammars/latex.json")),
        grammar(import("tm-grammars/grammars/typst.json")),
        grammar(import("tm-grammars/grammars/markdown.json")),
      ]),
      engine: createJavaScriptRegexEngine(),
    });
  })();
  // a highlighter which cannot be created is created again by the next code
  highlighter.catch(() => {
    highlighter = null;
  });
  return highlighter;
}

/** The code as highlighted HTML, a `<pre>` of Shiki, which escapes the code; `null` for a code
 * above `HIGHLIGHT_LIMIT`, which the view shows as text. */
export async function highlight(code: string, format: OdeFormat): Promise<string | null> {
  if (code.length > HIGHLIGHT_LIMIT) return null;
  return (await load()).codeToHtml(code, { lang: LANGUAGES[format], theme: THEME });
}
