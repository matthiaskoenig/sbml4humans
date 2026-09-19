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

/** The only schemes a link of a description may use. markdown-it's own `validateLink` is a
 * denylist (it refuses `vbscript:`, `javascript:`, `file:` and most `data:` urls and nothing
 * else), so every other scheme, and a relative url with no scheme at all (`page.md`, `#anchor`,
 * `/path`), would otherwise pass through unchanged. The generator that writes the glossary always
 * rewrites a description's links to `glossary:<key>` or to an absolute `https:` url; a relative
 * url in the details json is therefore a generator bug, not a link this module should ever turn
 * into a live href of its own app. `validateLink` below replaces the denylist with this allowlist,
 * so a link of any other scheme, and a relative url, render as their own source text instead. */
const ALLOWED_SCHEMES = [GLOSSARY_SCHEME, "https:", "http:", "mailto:"] as const;

const md: MarkdownItInstance = new MarkdownIt({ html: false, linkify: false, typographer: false });

md.validateLink = (url: string): boolean => {
  const trimmed = url.trim();
  const lower = trimmed.toLowerCase();
  const scheme = ALLOWED_SCHEMES.find((candidate) => lower.startsWith(candidate));
  if (scheme === undefined) return false;
  // a `glossary:` link with nothing after the scheme names no entry; refusing it here, rather
  // than in `linkOpen` below, means markdown-it never creates a token for it in the first place,
  // so no state has to track which link was refused across the `link_open`/`link_close` pair.
  if (scheme === GLOSSARY_SCHEME && trimmed.length === scheme.length) return false;
  return true;
};

interface RenderEnv extends Env {
  /** The href of the entry a `glossary:<key>` link of the description being rendered points at,
   * given by the caller of `renderHelpMarkdown` so this module stays free of the router. */
  hrefOf: (key: string) => string;
}

// `validateLink` above already refused every link that is not a `glossary:` link with a key, or
// an `https:`, `http:` or `mailto:` link: markdown-it never creates a `link_open` token for
// anything else, so this rule needs no state of its own and no matching `link_close` override,
// unlike an earlier version of this module which tracked a dropped link across the two rules.
const linkOpen: RendererRule = (tokens, idx, options, env, self) => {
  const token = tokens[idx]!;
  // `attrGet` answers `string | number | null` (a numeric attribute value, a table cell's
  // `colspan`, is possible in general; a link's `href` never is one), so this normalises it to
  // the string every check below expects.
  const href = String(token.attrGet("href") ?? "");
  if (href.startsWith(GLOSSARY_SCHEME)) {
    const key = href.slice(GLOSSARY_SCHEME.length);
    token.attrSet("href", (env as RenderEnv).hrefOf(key));
    token.attrSet("data-help-key", key);
    token.attrSet("class", "help-link");
    return self.renderToken(tokens, idx, options);
  }
  // an https:, http: or mailto: link (the specification, the documentation site, ...) opens in a
  // new tab, so a reader never loses the report behind it
  token.attrSet("target", "_blank");
  token.attrSet("rel", "noopener");
  return self.renderToken(tokens, idx, options);
};

md.renderer.rules.link_open = linkOpen;

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
    // no description carries an image (the survey of the real glossary found none), so `img` is
    // left out on purpose, not merely forgotten: markdown-it would otherwise turn `![x](url)` into
    // one, `src` is not in `ALLOWED_ATTR` below, and an `img` without a `src` is still an element
    // worth not having in a dialog whose only job is explaining text.
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
