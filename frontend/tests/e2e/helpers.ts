import { expect, type Page } from "@playwright/test";

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
