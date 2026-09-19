import { APP_COMMIT, APP_VERSION } from "@/build";
import { REPOSITORY_URL } from "@/repository";
import type { ReportSource } from "@/stores/report";

/** What a new issue says about where it was opened. */
export interface FeedbackContext {
  /** The path of the route with its query, e.g. `/examples/repressilator?pk=...`. */
  fullPath: string;
  /** The path of the route alone. */
  path: string;
  /** The source of the report which is shown, null on a page without a report. */
  source: ReportSource | null;
}

/** The report a reader gives feedback on, as far as it is public: an example and a model behind
 * a url can be opened by whoever reads the issue, so the issue names them and the view of the
 * route, which holds the selected element. A file, pasted content and a local report are the
 * reader's own, and neither their name nor the ids of their elements, which the query of the
 * route carries, are written into an issue for them. */
function reportLines(context: FeedbackContext): string[] {
  const { source } = context;
  if (!source) return [`- page: \`${context.path}\``];
  if (source.kind === "example") {
    return [`- page: \`${context.fullPath}\``, `- model: the example \`${source.id ?? ""}\``];
  }
  if (source.kind === "url") {
    return [`- page: \`${context.fullPath}\``, `- model: ${source.url ?? ""}`];
  }
  return [`- page: \`${context.path}\``, "- model: a file of my own"];
}

/** The url which opens a new issue of the repository with what a maintainer asks first already
 * written: the version and the commit of the build, the page, the model and the browser. The
 * reader sees the text before they submit it and can take out what they do not want to share. */
export function issueUrl(context: FeedbackContext): string {
  const build = APP_COMMIT ? `${APP_VERSION} (${APP_COMMIT.slice(0, 7)})` : APP_VERSION;
  const body = [
    "<!-- What did you see, and what did you expect? A screenshot helps. -->",
    "",
    "",
    "---",
    `- SBML4Humans ${build}`,
    ...reportLines(context),
    `- browser: ${navigator.userAgent}`,
  ].join("\n");
  return `${REPOSITORY_URL}/issues/new?${new URLSearchParams({ body }).toString()}`;
}
