import { readdirSync, readFileSync } from "node:fs";

/** The api the end to end tests run against, the backend started with
 * `SBML4HUMANS_ALLOW_PRIVATE_URLS=1` on port 1444. */
const API_URL = "http://localhost:1444/api";
const SPECS_DIR = new URL("./", import.meta.url);

/** Every string of the specs, decoded where it is a part of a url: the ids of the examples they
 * open are among them. */
function stringsOfSpecs(): Set<string> {
  const strings = new Set<string>();
  for (const name of readdirSync(SPECS_DIR)) {
    if (!name.endsWith(".spec.ts")) continue;
    const source = readFileSync(new URL(name, SPECS_DIR), "utf8");
    for (const match of source.matchAll(/["'`]([^"'`\n]+)["'`]/g)) {
      strings.add(match[1]!);
      for (const part of match[1]!.split("/")) {
        try {
          strings.add(decodeURIComponent(part));
        } catch {
          // not a part of a url
        }
      }
    }
  }
  return strings;
}

/** Warm the report cache of the backend with the examples the specs open. The backend builds the
 * report of an example on the first request for it and keeps it, so building them before the
 * specs run takes that work out of the timeouts of the specs, whose parallel workers would
 * otherwise wait for the backend at once; the walk over every example builds the rest itself. */
export default async function globalSetup(): Promise<void> {
  const response = await fetch(`${API_URL}/examples`).catch(() => null);
  if (!response?.ok) {
    throw new Error(
      `the backend at ${API_URL} is not reachable: start it with ` +
        "`SBML4HUMANS_ALLOW_PRIVATE_URLS=1 uv run uvicorn sbml4humans.api:api --port 1444`",
    );
  }
  const { examples } = (await response.json()) as { examples: { id: string }[] };
  const used = stringsOfSpecs();
  // one at a time: building a report is CPU bound in the backend, in parallel they share it
  for (const { id } of examples.filter((example) => used.has(example.id))) {
    const report = await fetch(`${API_URL}/examples/${encodeURIComponent(id)}`);
    await report.arrayBuffer();
  }
}
