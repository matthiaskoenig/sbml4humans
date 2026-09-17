// Record the api responses of a few examples for the unit tests.
// Usage: start the backend (uv run uvicorn sbml4humans.api:api --port 1444), then `npm run fixtures`.
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const API_URL = process.env.VITE_API_URL ?? "http://localhost:1444/api";
const FIXTURES_DIR = fileURLToPath(new URL("../tests/fixtures/", import.meta.url));

/** fixture name -> example id */
const EXAMPLES = {
  repressilator: "BIOMD0000000012",
  icg_body: "icg_body (icg_body.xml)",
  fbc_example: "fbc_example (fbc_example.xml)",
  model_definitions: "model_definitions (model_definitions.xml)",
  comp_models: "CompModels",
  distrib_uncertainties: "distrib_uncertainties (distrib_uncertainties.xml)",
};

async function fetchJson(path) {
  const response = await fetch(`${API_URL}${path}`);
  const body = await response.json();
  if (Array.isArray(body.errors) && body.errors.length > 0) {
    throw new Error(`${path}: ${body.errors[0]}`);
  }
  return body;
}

await mkdir(FIXTURES_DIR, { recursive: true });
const examples = await fetchJson("/examples");
await writeFile(`${FIXTURES_DIR}examples.json`, JSON.stringify(examples.examples, null, 2));
console.log(`examples.json: ${examples.examples.length} examples`);

for (const [name, id] of Object.entries(EXAMPLES)) {
  const report = await fetchJson(`/examples/${encodeURIComponent(id)}`);
  await writeFile(`${FIXTURES_DIR}${name}.json`, JSON.stringify(report, null, 2));
  console.log(`${name}.json: ${Object.keys(report.reports).join(", ")}`);
}
