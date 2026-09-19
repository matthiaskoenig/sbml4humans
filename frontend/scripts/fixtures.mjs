// Record the api responses of a few examples for the unit tests.
// Usage: start the backend (uv run uvicorn sbml4humans.api:api --port 1444), then `npm run fixtures`.
// Names given as arguments record those fixtures alone (`npm run fixtures -- repressilator`),
// which keeps the other recordings, and with them the order of the entries of an archive, as
// they are.
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const API_URL = process.env.VITE_API_URL ?? "http://localhost:1444/api";
const FIXTURES_DIR = fileURLToPath(new URL("../tests/fixtures/", import.meta.url));

/** fixture name -> example id */
const EXAMPLES = {
  repressilator: "BIOMD0000000012",
  cell_cycle: "BIOMD0000000007",
  icg_body: "icg_body (icg_body.xml)",
  fbc_example: "fbc_example (fbc_example.xml)",
  fbc_bounds_v1: "fbc_bounds_v1 (fbc_bounds_v1.xml)",
  fbc_constraints_v3: "fbc_constraints_v3 (fbc_constraints_v3.xml)",
  model_definitions: "model_definitions (model_definitions.xml)",
  comp_deletion: "comp_deletion (comp_deletion.xml)",
  comp_models: "CompModels",
  distrib_uncertainties: "distrib_uncertainties (distrib_uncertainties.xml)",
  distrib_spans: "distrib_spans (distrib_spans.xml)",
  qual_example: "qual_example (qual_example.xml)",
  constraint_event: "constraint_event (constraint_event.xml)",
};

const requested = process.argv.slice(2);
const unknown = requested.filter((name) => !(name in EXAMPLES));
if (unknown.length > 0) {
  console.error(
    `unknown fixture ${unknown.join(", ")}, known are ${Object.keys(EXAMPLES).join(", ")}`,
  );
  process.exit(1);
}
const selected = requested.length > 0 ? requested : Object.keys(EXAMPLES);

async function fetchJson(path) {
  const response = await fetch(`${API_URL}${path}`);
  const body = await response.json();
  if (Array.isArray(body.errors) && body.errors.length > 0) {
    throw new Error(`${path}: ${body.errors[0]}`);
  }
  return body;
}

await mkdir(FIXTURES_DIR, { recursive: true });
if (requested.length === 0) {
  const examples = await fetchJson("/examples");
  await writeFile(`${FIXTURES_DIR}examples.json`, JSON.stringify(examples.examples, null, 2));
  console.log(`examples.json: ${examples.examples.length} examples`);
}

for (const name of selected) {
  const id = EXAMPLES[name];
  const report = await fetchJson(`/examples/${encodeURIComponent(id)}`);
  await writeFile(`${FIXTURES_DIR}${name}.json`, JSON.stringify(report, null, 2));
  console.log(`${name}.json: ${Object.keys(report.reports).join(", ")}`);
}
