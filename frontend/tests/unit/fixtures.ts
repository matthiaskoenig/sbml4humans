/// <reference types="node" />
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import type {
  EntryValidation,
  ExampleMetaData,
  Report,
  ReportResponse,
  ValidationIssue,
  ValidationResponse,
} from "@/api/types";

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
  | "list_of"
  | "fan_out";

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

/** The fixtures whose validation is recorded as well, as `validation-<name>.json`. */
export type ValidatedFixtureName = "validation" | "repressilator" | "fan_out";

export function loadValidationFixture(name: ValidatedFixtureName): ValidationResponse {
  const path = join(FIXTURES_DIR, `validation-${name}.json`);
  return JSON.parse(readFileSync(path, "utf8")) as ValidationResponse;
}

/** The validation of the first (or given) entry of a fixture. */
export function loadValidation(name: ValidatedFixtureName, location?: string): EntryValidation {
  const response = loadValidationFixture(name);
  const key = location ?? Object.keys(response.entries)[0];
  const entry = key === undefined ? undefined : response.entries[key];
  if (!entry) throw new Error(`validation fixture ${name} has no entry ${location}`);
  return entry;
}

/** A validation which holds the given issues: each names its element and severity, the rule and
 * the texts default to a plain warning of units. */
export function withIssues(
  issues: (Pick<ValidationIssue, "pk" | "severity"> & Partial<ValidationIssue>)[],
  skipped: EntryValidation["skipped"] = null,
): EntryValidation {
  return {
    skipped,
    issues: issues.map((issue) => ({
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
