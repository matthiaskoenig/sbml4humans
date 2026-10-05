/// <reference types="node" />
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import type { ExampleMetaData, Report, ReportResponse, ValidationIssue } from "@/api/types";

// `new URL(x, import.meta.url)` is Vite's static asset-url pattern: it rewrites the call at
// transform time, which mangles a runtime path built from a template literal. Building the
// fixtures directory once with node:path/node:url instead keeps this a plain Node file read.
const FIXTURES_DIR = join(dirname(fileURLToPath(import.meta.url)), "..", "fixtures");

export type FixtureName =
  | "repressilator"
  | "cell_cycle"
  | "icg_body"
  | "fbc_example"
  | "fbc_bounds_v1"
  | "fbc_constraints_v3"
  | "model_definitions"
  | "comp_deletion"
  | "validation"
  | "comp_models"
  | "distrib_uncertainties"
  | "distrib_spans"
  | "constraint_event"
  | "qual_example"
  | "list_of";

export function loadFixture(name: FixtureName): ReportResponse {
  const path = join(FIXTURES_DIR, `${name}.json`);
  return JSON.parse(readFileSync(path, "utf8")) as ReportResponse;
}

/** The report of the first (or given) entry of a fixture. */
export function loadReport(name: FixtureName, location?: string): Report {
  const response = loadFixture(name);
  const key = location ?? Object.keys(response.reports)[0];
  const entry = key === undefined ? undefined : response.reports[key];
  if (!entry) throw new Error(`fixture ${name} has no entry ${location}`);
  return entry.report;
}

export function loadExamplesFixture(): ExampleMetaData[] {
  const path = join(FIXTURES_DIR, "examples.json");
  return JSON.parse(readFileSync(path, "utf8")) as ExampleMetaData[];
}

/** A copy of a report whose validation holds the given issues in place of its own: each names its
 * element and severity, the rule and the texts default to a plain warning of units. */
export function withIssues(
  report: Report,
  issues: (Pick<ValidationIssue, "pk" | "severity"> & Partial<ValidationIssue>)[],
  validationSkipped: Report["validationSkipped"] = null,
): Report {
  return {
    ...report,
    validationSkipped,
    validation: issues.map((issue) => ({
      rule: 99505,
      category: "Units consistency",
      shortMessage: `an issue of ${issue.pk}`,
      message: `The message of an issue of ${issue.pk}.`,
      line: 0,
      column: 0,
      ...issue,
    })),
  };
}
