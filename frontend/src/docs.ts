/** The base url of the documentation site, e.g. to build the url of a reference page.
 * Vitest does not load `.env.development`, so an unset and an empty `VITE_DOCS_URL` both fall
 * back to the site's own default instead of building a relative, broken link.
 *
 * It lives apart from `report/glossary.ts`, so that the app bar and the footer of every page
 * link the site without carrying the glossary, which the report alone needs. */
export const DOCS_URL: string =
  (import.meta.env.VITE_DOCS_URL as string | undefined)?.trim() ||
  "https://matthiaskoenig.github.io/sbml4humans/";
