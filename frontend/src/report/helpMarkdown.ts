import DOMPurify from "dompurify";
import MarkdownIt, {
  type Env,
  type MarkdownIt as MarkdownItInstance,
  type RendererRule,
} from "markdown-it";

/** This module owns the only `markdown-it` instance of the frontend, and its own DOMPurify
 * instance, so its hooks and rules never apply to another use of the shared default instance
 * (`report/notes.ts` does the same for the xhtml of an SBase's notes). Nothing outside
 * `components/help/HelpMarkdown.vue` imports this module: `markdown-it` is loaded only once a
 * reader opens the help dialog, never with the entry chunk every page pays for. */

/** The scheme a description uses to link to another entry of the glossary, `glossary:<key>`. */
const GLOSSARY_SCHEME = "glossary:";

const md: MarkdownItInstance = new MarkdownIt({ html: false, linkify: false, typographer: false });

// markdown-it's default `validateLink` refuses a scheme it does not know (it already allows
// `https:`, `http:` and `mailto:`); accept `glossary:` too, so a description can link to another
// entry of the glossary. `html: false` above is the first line of defence against raw html in a
// description, escaping it to text; the DOMPurify pass below is the second.
const validatesKnownScheme = md.validateLink.bind(md);
md.validateLink = (url: string): boolean =>
  url.startsWith(GLOSSARY_SCHEME) || validatesKnownScheme(url);

/** Whether the link a `link_open` token about to render is a `glossary:` link with no key, so its
 * matching `link_close` drops the closing tag too and only the link text is left. One instance
 * renders one description at a time, synchronously, so a plain stack shared by the two rules is
 * enough: markdown forbids a link inside a link, so opens and closes always nest correctly. */
const droppedLinks: boolean[] = [];

interface RenderEnv extends Env {
  /** The href of the entry a `glossary:<key>` link of the description being rendered points at,
   * given by the caller of `renderHelpMarkdown` so this module stays free of the router. */
  hrefOf: (key: string) => string;
}

const linkOpen: RendererRule = (tokens, idx, options, env, self) => {
  const token = tokens[idx]!;
  // `attrGet` answers `string | number | null` (a numeric attribute value, a table cell's
  // `colspan`, is possible in general; a link's `href` never is one), so this normalises it to
  // the string every check below expects.
  const href = String(token.attrGet("href") ?? "");
  if (href.startsWith(GLOSSARY_SCHEME)) {
    const key = href.slice(GLOSSARY_SCHEME.length);
    if (!key) {
      droppedLinks.push(true);
      return "";
    }
    token.attrSet("href", (env as RenderEnv).hrefOf(key));
    token.attrSet("data-help-key", key);
    token.attrSet("class", "help-link");
    droppedLinks.push(false);
    return self.renderToken(tokens, idx, options);
  }
  // an external link (the specification, the documentation site, ...) opens in a new tab, so a
  // reader never loses the report behind it
  token.attrSet("target", "_blank");
  token.attrSet("rel", "noopener");
  droppedLinks.push(false);
  return self.renderToken(tokens, idx, options);
};

const linkClose: RendererRule = (tokens, idx, options, _env, self) =>
  droppedLinks.pop() ? "" : self.renderToken(tokens, idx, options);

md.renderer.rules.link_open = linkOpen;
md.renderer.rules.link_close = linkClose;

/** This module's own DOMPurify instance, restricted to the markup real descriptions use. */
const purifier = DOMPurify(window);

/** Renders the markdown of one glossary entry's `description` into sanitised html for use with
 * `v-html`. `hrefOf(key)` answers the href of the entry a `[label](glossary:key)` link points at;
 * the rendered anchor carries that href, `data-help-key="key"` and `class="help-link"`, so
 * `HelpMarkdown.vue` can tell an in-app link from an external one without parsing the href again.
 * A `glossary:` link with an empty key, and a link whose scheme is none of `glossary:`, `https:`,
 * `http:` or `mailto:`, are rendered as their plain text, not as a link. */
export function renderHelpMarkdown(markdown: string, hrefOf: (key: string) => string): string {
  const html = md.render(markdown, { hrefOf } satisfies RenderEnv);
  return purifier.sanitize(html, {
    ALLOWED_TAGS: [
      "p",
      "em",
      "strong",
      "code",
      "pre",
      "ul",
      "ol",
      "li",
      "a",
      "br",
      "table",
      "thead",
      "tbody",
      "tr",
      "th",
      "td",
    ],
    ALLOWED_ATTR: ["href", "rel", "class", "data-help-key"],
    ADD_ATTR: ["target"],
  });
}
