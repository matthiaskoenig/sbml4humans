import type { ResolutionStatus } from "@/api/types";

/** What the inspector shows for the status of an external model definition. The explanation of
 * every status is the glossary entry of the field, which the label of its row links. */
export const RESOLUTION_STATUS_LABELS: Readonly<Record<ResolutionStatus, string>> = {
  resolved: "resolved",
  remoteSource: "remote source, not fetched",
  notFound: "no document at the source",
  notSbml: "no SBML model at the source",
  modelNotFound: "model not found in the document",
  circular: "circular chain of definitions",
};
