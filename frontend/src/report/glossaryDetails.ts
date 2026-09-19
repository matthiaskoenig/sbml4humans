/** The long description and the technical detail of every entry of the glossary, kept apart from
 * `glossary.json` (`glossary.ts`) because a dialog needs it only once a reader opens one, while
 * the label and the summary every tooltip shows have to be there from the first render. */

/** The kind of thing an entry explains, the same four the eager glossary groups entries into,
 * plus the data types of the specification, which only the details carry. */
export type HelpKind = "type" | "attribute" | "link" | "concept" | "datatype";

/** One validation rule of the SBML specification a type or an attribute is held to. */
export interface HelpRule {
  id: number;
  severity: "error" | "warning";
  message: string;
  section?: string;
}

/** The full explanation of one entry of the glossary, keyed by `GlossaryDetails.entries`. Every
 * entry carries `kind`, `label`, `summary`, `description` (markdown whose links to another entry
 * are `glossary:<key>`), `package` and `docs`; the rest applies where the kind of the entry has
 * it, for example an attribute alone carries `owner`, `type`, `required` and `default`. */
export interface HelpEntry {
  kind: HelpKind;
  label: string;
  summary: string;
  description: string;
  package: string;
  docs: string;
  owner?: string;
  type?: { label: string; key: string };
  spec?: { label: string; section?: string; url: string };
  required?: boolean;
  default?: string;
  values?: string[];
  rules?: HelpRule[];
  related?: string[];
  attributes?: string[];
}

/** The whole details file, `{"entries": {key: entry}}`, keys sorted. */
export interface GlossaryDetails {
  entries: Record<string, HelpEntry>;
}

/** The cached promise of the loaded details, so that every dialog which opens after the first
 * shares one fetch instead of importing the file again; reset when the import rejects, so that a
 * reader who opens a dialog after a failed load (for example while offline) gets a fresh attempt
 * rather than a promise stuck forever in its rejected state. */
let cachedDetails: Promise<GlossaryDetails> | undefined;

/** Loads `glossary-details.json` behind a dynamic `import()`, the only reference to that file in
 * the frontend, so that Vite puts its 300+ KB into a chunk of its own instead of the entry chunk
 * every page pays for. Call it when a dialog is about to open, never at module load. */
export function loadGlossaryDetails(): Promise<GlossaryDetails> {
  if (!cachedDetails) {
    cachedDetails = import("@/data/glossary-details.json").then(
      (module) => module.default as GlossaryDetails,
    );
    cachedDetails.catch(() => {
      cachedDetails = undefined;
    });
  }
  return cachedDetails;
}
