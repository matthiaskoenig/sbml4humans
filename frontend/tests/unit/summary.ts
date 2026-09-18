import { expect } from "vitest";

import type { GlossaryEntry } from "@/report/glossary";

/** The summary of a glossary entry, which a tooltip has to show. It fails when the entry or its
 * summary is gone, so that a test cannot pass by comparing a tooltip that is not shown with a
 * summary that does not exist: both are `undefined`. */
export function summaryOf(entry: GlossaryEntry | undefined, what: string): string {
  const summary = entry?.summary;
  expect(summary, `the glossary has no entry for ${what}`).toBeTypeOf("string");
  expect(summary, `the glossary entry of ${what} has an empty summary`).not.toBe("");
  return summary!;
}
