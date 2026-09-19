import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

import { REPOSITORY, query } from "./helpers";

// `/report?local=<token>` is the address `sbml4humans.show` of the python package opens: the
// report of a file of the machine, which its local server built and holds under the token. The
// local server is no part of this test, which answers its two endpoints itself; the `package`
// job of the CI runs the real one from the wheel.
const REPORT = readFileSync(`${REPOSITORY}frontend/tests/fixtures/comp_deletion.json`, "utf8");

test("the report of a local token is shown and keeps its token while it is read", async ({
  page,
}) => {
  const requested: string[] = [];
  await page.route("**/api/local/reports/*", async (route) => {
    requested.push(new URL(route.request().url()).pathname);
    await route.fulfill({ contentType: "application/json", body: REPORT });
  });
  await page.goto("/report?local=token1");
  await expect(page.getByTestId("report-page")).toBeVisible();
  expect(requested).toEqual(["/api/local/reports/token1"]);
  // the file of the user and the file next to it which its external model definition names
  const entries = page.getByRole("combobox", { name: "archive entry", exact: true });
  await expect(entries).toHaveValue("./comp_deletion.xml");

  // selecting an element, and following a link into the other entry, keep the token
  await page.locator('tbody tr[data-pk$="Submodel:unit_library"] td').first().click();
  expect(query(page, "local")).toBe("token1");
  await page
    .getByTestId("inspector")
    .locator('[data-entry="./unit_definitions.xml"]')
    .first()
    .click();
  await expect(entries).toHaveValue("./unit_definitions.xml");
  expect(query(page, "local")).toBe("token1");
  expect(requested).toHaveLength(1);

  // a reload reads the report again: it lives on the local server and not in the page
  await page.reload();
  await expect(page.getByTestId("report-page")).toBeVisible();
  expect(requested).toHaveLength(2);
});

test("a token the local server does not know says how to get the report again", async ({
  page,
}) => {
  await page.route("**/api/local/reports/*", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        errors: ["There is no report for the token of this address (any more).", ""],
        warnings: [],
        info: {},
      }),
    }),
  );
  await page.goto("/report?local=gone");
  await expect(page.getByTestId("error-state")).toContainText("no report for the token");
});
