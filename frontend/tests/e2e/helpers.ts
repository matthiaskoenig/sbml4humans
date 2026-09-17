import { expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";

export const REPOSITORY = new URL("../../../", import.meta.url).pathname;
export const REPRESSILATOR_FILE = `${REPOSITORY}backend/sbml4humans/resources/models/repressilator/BIOMD0000000012_urn.xml`;

/** Open the report of an example and wait for the tables. */
export async function openExample(page: Page, id: string): Promise<void> {
  await page.goto(`/examples/${encodeURIComponent(id)}`);
  await expect(page.getByTestId("report-page")).toBeVisible();
}

export function query(page: Page, key: string): string | null {
  return new URL(page.url()).searchParams.get(key);
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
