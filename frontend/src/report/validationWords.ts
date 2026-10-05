import type { EntrySkip } from "@/report/validationIndex";

/** Why libsbml did not check a document, in two forms: `short` is the tooltip of the chip of the
 * app bar, `long` the note of the list of issues in the inspector of the document. No severity of
 * libsbml, the check did not run. */
export interface SkipWords {
  short: string;
  long: string;
}

const PREFIX = "libsbml did not check this document:";

const WORDS: Record<Exclude<EntrySkip, "busy">, SkipWords> = {
  expandedSize: {
    short: `${PREFIX} its comp submodels expand it beyond the size which is checked`,
    long: `${PREFIX} its comp submodels expand it to more elements than are checked in a bounded time. Only the errors of reading the file are listed.`,
  },
  timeout: {
    short: `${PREFIX} the check did not end in time`,
    long: `${PREFIX} the check did not end in the time a validation may take.`,
  },
  memory: {
    short: `${PREFIX} the check needed more memory than it may use`,
    long: `${PREFIX} the check needed more memory than a validation may use.`,
  },
  crashed: {
    short: `${PREFIX} the check ended abnormally`,
    long: `${PREFIX} the process of the check ended abnormally on the server.`,
  },
  unanswered: {
    short: `${PREFIX} the validation answered nothing for it`,
    long: `${PREFIX} the answer of the validation left it out, so nothing is known of its consistency.`,
  },
};

/** A busy server is asked again by a reload, unless the source is a file or pasted content, which
 * a reload loses (`ValidationIndex.reloadable`). */
function busyWords(reloadable: boolean): SkipWords {
  return reloadable
    ? {
        short: `${PREFIX} the server was busy, reload the report later to try again`,
        long: `${PREFIX} the server was busy with other validations. Reload the report later to try again.`,
      }
    : {
        short: `${PREFIX} the server was busy, load it again later to try again`,
        long: `${PREFIX} the server was busy with other validations. Load it again later to try again.`,
      };
}

/** The words of why a document was not checked. */
export function skipWords(reason: EntrySkip, reloadable: boolean): SkipWords {
  return reason === "busy" ? busyWords(reloadable) : WORDS[reason];
}
