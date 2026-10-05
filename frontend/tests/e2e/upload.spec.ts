import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

import { expectReport, query, REPOSITORY } from "./helpers";

// `/report?upload=<id>` is the address other tools (cy3sbml) open after `POST /api/upload`: the
// backend keeps the upload for 24 hours. The test answers the endpoint itself.
const REPORT = readFileSync(`${REPOSITORY}frontend/tests/fixtures/comp_deletion.json`, "utf8");
/** The validation of the upload, which the page requests with the same id: both entries valid. */
const VALIDATION = {
  entries: {
    "./comp_deletion.xml": { issues: [], skipped: null },
    "./unit_definitions.xml": { issues: [], skipped: null },
  },
  skipped: null,
};

test("the report of an upload keeps its id while it is read and after a reload", async ({
  page,
}) => {
  const requested: string[] = [];
  await page.route("**/api/upload/*", async (route) => {
    requested.push(new URL(route.request().url()).pathname);
    await route.fulfill({ contentType: "application/json", body: REPORT });
  });
  await page.route("**/api/validation/upload/*", async (route) => {
    requested.push(new URL(route.request().url()).pathname);
    await route.fulfill({ json: VALIDATION });
  });
  await page.goto("/report?upload=upload1");
  await expectReport(page);
  await expect(page.getByTestId("validation-pending")).toHaveCount(0);
  await expect(page.getByTestId("validation-failed")).toHaveCount(0);
  expect(requested).toEqual(["/api/upload/upload1", "/api/validation/upload/upload1"]);

  await page.locator('tbody tr[data-pk$="Submodel:unit_library"] td').first().click();
  expect(query(page, "upload")).toBe("upload1");
  expect(requested).toHaveLength(2);

  await page.reload();
  await expectReport(page);
  await expect(page.getByTestId("validation-pending")).toHaveCount(0);
  expect(requested).toHaveLength(4);
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
