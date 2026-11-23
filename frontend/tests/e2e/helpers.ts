import { expect, type Locator, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";

export const REPOSITORY = new URL("../../../", import.meta.url).pathname;
export const REPRESSILATOR_FILE = `${REPOSITORY}backend/sbml4humans/resources/models/repressilator/BIOMD0000000012_urn.xml`;

/** Wait for the report page of a report which was requested. Creating a report is CPU bound in
 * the backend, and the parallel workers of the other specs compete for the machine, so the wait
 * is longer than the ten seconds of the configured expect timeout by default; a report which
 * takes even longer, an archive of several entries or a model of thousands of elements, passes
 * its own `timeout`. */
export async function expectReport(page: Page, timeout = 30_000): Promise<void> {
  await expect(page.getByTestId("report-page")).toBeVisible({ timeout });
}

/** Open the report of an example and wait for the tables (`expectReport`). */
export async function openExample(page: Page, id: string, timeout = 30_000): Promise<void> {
  await page.goto(`/examples/${encodeURIComponent(id)}`);
  await expectReport(page, timeout);
}

/** Paste SBML on the home page and wait for its report (`expectReport`). */
export async function paste(page: Page, sbml: string): Promise<void> {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(sbml);
  await page.getByTestId("paste-submit").click();
  await expectReport(page);
}

/** A comp document whose main model expands to `n` submodels on each of `depth` levels. Five
 * levels of ten expand 3 KB to 222,268 elements: more than the comp validator checks, and more
 * than the flattening of the equations fits in the memory of the backend. The document is the
 * one of `_fan_out` of `backend/tests/conftest.py` and of `fanOut` of `frontend/scripts/fixtures.mjs`,
 * down to the parameter of its main model, so that every suite states the same number of
 * elements. */
export function fanOut(depth: number, n: number): string {
  const submodels = (ref: string) =>
    "<comp:listOfSubmodels>" +
    Array.from(
      { length: n },
      (_, i) => `<comp:submodel comp:id="s${i}" comp:modelRef="${ref}"/>`,
    ).join("") +
    "</comp:listOfSubmodels>";
  const definitions = Array.from({ length: depth }, (_, k) =>
    k === 0
      ? '<comp:modelDefinition id="d0"/>'
      : `<comp:modelDefinition id="d${k}">${submodels(`d${k - 1}`)}</comp:modelDefinition>`,
  ).join("");
  return (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" ' +
    'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" ' +
    'level="3" version="1" comp:required="true">' +
    '<model id="m"><listOfParameters>' +
    '<parameter id="p" value="1" constant="true"/></listOfParameters>' +
    `${submodels(`d${depth - 1}`)}</model>` +
    `<comp:listOfModelDefinitions>${definitions}</comp:listOfModelDefinitions></sbml>`
  );
}

/** Search the report and wait until the search is applied. The search box applies what is typed
 * after a short pause, and the tables shrink to the matches then: a click in that pause lands on
 * the row which the shrinking tables move under the pointer. */
export async function search(page: Page, text: string): Promise<void> {
  await page.getByTestId("search-input").fill(text);
  await expect.poll(() => query(page, "q")).toBe(text);
}

export function query(page: Page, key: string): string | null {
  return new URL(page.url()).searchParams.get(key);
}

/** The attribute row of the inspector whose label is this field, the way `report.spec.ts` picks a
 * row by the text it carries; the field names of the repressilator this file uses share no
 * substring with one another, so the row's whole text (its label and its value together) is
 * enough to tell them apart. */
export function attributeRow(scope: Locator, field: string): Locator {
  return scope.getByTestId("attribute-row").filter({ hasText: field });
}

/** A local http server for the repressilator model, so the url input is tested without an
 * external host: the backend downloads the url and runs on this machine. */
export async function serveModel(): Promise<{ url: string; close: () => Promise<void> }> {
  const body = readFileSync(REPRESSILATOR_FILE);
  const server = createServer((_request, response) => {
    response.writeHead(200, { "content-type": "application/xml" });
    response.end(body);
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  if (address === null || typeof address === "string") throw new Error("the server has no port");
  return {
    url: `http://127.0.0.1:${address.port}/BIOMD0000000012_urn.xml`,
    close: () =>
      new Promise<void>((resolve, reject) => {
        // the backend keeps the connection of its download alive, it never ends the server itself
        server.closeAllConnections();
        server.close((error) => (error ? reject(error) : resolve()));
      }),
  };
}
