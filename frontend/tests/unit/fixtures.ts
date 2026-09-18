/// <reference types="node" />
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import type { ExampleMetaData, Report, ReportResponse } from "@/api/types";

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
  | "comp_models"
  | "distrib_uncertainties"
  | "distrib_spans"
  | "constraint_event"
  | "qual_example";

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
