// Record the api responses of a few examples for the unit tests: the report of every fixture,
// and for those of `VALIDATED` the validation as `validation-<name>.json`.
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
  validation: "validation (validation.xml)",
  comp_models: "CompModels",
  distrib_uncertainties: "distrib_uncertainties (distrib_uncertainties.xml)",
  distrib_spans: "distrib_spans (distrib_spans.xml)",
  qual_example: "qual_example (qual_example.xml)",
  constraint_event: "constraint_event (constraint_event.xml)",
  list_of: "list_of (list_of.xml)",
};

const COMP_SBML =
  '<?xml version="1.0" encoding="UTF-8"?>' +
  '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" ' +
  'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" ' +
  'level="3" version="1" comp:required="true">';

/** A list of `n` submodels of one model. */
function submodels(modelRef, n) {
  const items = Array.from(
    { length: n },
    (_, i) => `<comp:submodel comp:id="s${i}" comp:modelRef="${modelRef}"/>`,
  );
  return `<comp:listOfSubmodels>${items.join("")}</comp:listOfSubmodels>`;
}

/**
 * A main model of ten submodels on five levels, 3 KB which expand to more than 100,000
 * instances: beyond the budget of the validation, which skips it.
 */
function fanOut() {
  const definitions = ['<comp:modelDefinition id="d0"/>'];
  for (let k = 1; k < 5; k++) {
    definitions.push(
      `<comp:modelDefinition id="d${k}">${submodels(`d${k - 1}`, 10)}</comp:modelDefinition>`,
    );
  }
  return (
    COMP_SBML +
    '<model id="m"><listOfParameters><parameter id="p" value="1" constant="true"/>' +
    `</listOfParameters>${submodels("d4", 10)}</model>` +
    `<comp:listOfModelDefinitions>${definitions.join("")}</comp:listOfModelDefinitions></sbml>`
  );
}

/** fixture name -> SBML content, posted to the content endpoints */
const CONTENTS = {
  fan_out: fanOut,
};

/** the fixtures whose validation is recorded as well */
const VALIDATED = new Set(["validation", "repressilator", "fan_out"]);

const KNOWN = [...Object.keys(EXAMPLES), ...Object.keys(CONTENTS)];
const requested = process.argv.slice(2);
const unknown = requested.filter((name) => !KNOWN.includes(name));
if (unknown.length > 0) {
  console.error(`unknown fixture ${unknown.join(", ")}, known are ${KNOWN.join(", ")}`);
  process.exit(1);
}
const selected = requested.length > 0 ? requested : KNOWN;

async function fetchJson(path, init) {
  const response = await fetch(`${API_URL}${path}`, init);
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
  let report;
  let validation;
  if (name in CONTENTS) {
    const init = { method: "POST", body: CONTENTS[name]() };
    report = await fetchJson("/content", init);
    if (VALIDATED.has(name)) validation = await fetchJson("/validation/content", init);
  } else {
    const id = encodeURIComponent(EXAMPLES[name]);
    report = await fetchJson(`/examples/${id}`);
    if (VALIDATED.has(name)) validation = await fetchJson(`/validation/examples/${id}`);
  }
  await writeFile(`${FIXTURES_DIR}${name}.json`, JSON.stringify(report, null, 2));
  console.log(`${name}.json: ${Object.keys(report.reports).join(", ")}`);
  if (validation !== undefined) {
    await writeFile(`${FIXTURES_DIR}validation-${name}.json`, JSON.stringify(validation, null, 2));
    const skipped = Object.values(validation.entries).map((entry) => entry.skipped ?? "validated");
    console.log(`validation-${name}.json: ${skipped.join(", ")}`);
  }
}
