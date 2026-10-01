import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

import { REPOSITORY, query } from "./helpers";

// `/report?upload=<id>` is the address other tools (cy3sbml) open after `POST /api/upload`: the
// backend keeps the upload for 24 hours. The test answers the endpoint itself.
const REPORT = readFileSync(`${REPOSITORY}frontend/tests/fixtures/comp_deletion.json`, "utf8");

test("the report of an upload keeps its id while it is read and after a reload", async ({
  page,
}) => {
  const requested: string[] = [];
  await page.route("**/api/upload/*", async (route) => {
    requested.push(new URL(route.request().url()).pathname);
    await route.fulfill({ contentType: "application/json", body: REPORT });
  });
  await page.goto("/report?upload=upload1");
  await expect(page.getByTestId("report-page")).toBeVisible();
  expect(requested).toEqual(["/api/upload/upload1"]);

  await page.locator('tbody tr[data-pk$="Submodel:unit_library"] td').first().click();
  expect(query(page, "upload")).toBe("upload1");
  expect(requested).toHaveLength(1);

  await page.reload();
  await expect(page.getByTestId("report-page")).toBeVisible();
  expect(requested).toHaveLength(2);
});

test("an expired upload says how long uploads are kept", async ({ page }) => {
  await page.route("**/api/upload/*", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        errors: ["The upload 'gone' is not available: uploads are kept for 24 hours.", ""],
        warnings: [],
        info: {},
      }),
    }),
  );
  await page.goto("/report?upload=gone");
  await expect(page.getByTestId("error-state")).toContainText("kept for 24 hours");
});
