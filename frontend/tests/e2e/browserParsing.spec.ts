import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";

import { expectReport, query, REPOSITORY } from "./helpers";

const MINIMAL = `${REPOSITORY}backend/sbml4humans/resources/examples/minimal_model.xml`;
const ARCHIVE = `${REPOSITORY}backend/sbml4humans/resources/omex/CompModels.omex`;

test.beforeEach(async ({ page }) => {
  // A local parse must succeed even when server report construction is unavailable.
  await page.route(/\/api\/(file|content)$/, (route) => route.abort());
});

for (const compressed of [false, true]) {
  test(`reads ${compressed ? "gzipped" : "plain"} SBML in the browser`, async ({ page }) => {
    const requests: string[] = [];
    page.on("request", (request) => {
      if (/\/api\/(file|content)$/.test(new URL(request.url()).pathname))
        requests.push(request.url());
    });
    await page.goto("/");
    await page.getByTestId("file-input").setInputFiles({
      name: compressed ? "model.xml.gz" : "model.xml",
      mimeType: "application/octet-stream",
      buffer: compressed ? gzipSync(readFileSync(MINIMAL)) : readFileSync(MINIMAL),
    });
    await expectReport(page);
    await expect(page.getByTestId("inspector-id")).toHaveText("minimal_model");
    await page.getByTestId("view-equations").click();
    await expect(page.getByTestId("equations-view")).toBeVisible();
    expect(requests).toEqual([]);
  });
}

test("follows an external model link in a locally parsed archive", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("file-input").setInputFiles(ARCHIVE);
  await expectReport(page);
  await page.getByTestId("entry-select").selectOption("./models/omex_comp.xml");
  await page.locator('tbody tr[data-pk="omex_comp/Species:S0"] td').first().click();
  const inspector = page.getByTestId("inspector");
  const target = inspector
    .getByTestId("attribute-row")
    .filter({
      has: page.locator("dt", { hasText: /^comp:listOfReplacedElements$/ }),
    })
    .getByTestId("nested-table")
    .locator("tbody tr")
    .first()
    .getByTestId("element-link")
    .last();
  await expect(target).toHaveAttribute("data-entry", "./models/omex_minimal.xml");
  await target.click();
  await expect.poll(() => query(page, "entry")).toBe("./models/omex_minimal.xml");
  await expect(inspector.getByTestId("inspector-id")).toHaveText("S1");
});

test("pasted content is reported locally and malformed input is shown inline", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill("<not-sbml/>");
  await page.getByTestId("paste-submit").click();
  await expect(page.getByTestId("error-state")).toBeVisible();
  await page.getByTestId("paste-input").fill(readFileSync(MINIMAL, "utf8"));
  await page.getByTestId("paste-submit").click();
  await expectReport(page);
});

test("cancels parser startup and can load again", async ({ page }) => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/*.wasm", async (route) => {
    await pending;
    await route.continue();
  });
  await page.goto("/");
  await page.getByTestId("file-input").setInputFiles(MINIMAL);
  await page.getByTestId("load-cancel").click();
  await expect(page.getByTestId("file-dropzone")).toBeVisible();
  await expect(page.getByTestId("error-state")).toHaveCount(0);
  release();
  await page.getByTestId("file-input").setInputFiles(MINIMAL);
  await expectReport(page);
});

test("allows worker WebAssembly under the production script policy", async ({ page }) => {
  const header = readFileSync(`${REPOSITORY}nginx/security-headers.conf`, "utf8");
  const policy = /add_header Content-Security-Policy "([^"]+)"/
    .exec(header)![1]!
    .replace(/; upgrade-insecure-requests(?=;|$)/, "");
  await page.route("**/", async (route) => {
    const response = await route.fetch();
    await route.fulfill({
      response,
      headers: { ...response.headers(), "content-security-policy": policy },
    });
  });
  await page.goto("/");
  await page.getByTestId("file-input").setInputFiles(MINIMAL);
  await expectReport(page);
});
