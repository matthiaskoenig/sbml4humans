import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

import { REPRESSILATOR_FILE, serveModel } from "./helpers";

let model: { url: string; close: () => Promise<void> };

test.beforeAll(async () => {
  model = await serveModel();
});

test.afterAll(async () => {
  await model.close();
});

test("uploads a file", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("file-input").setInputFiles(REPRESSILATOR_FILE);
  // the report opens with its model selected, which the url says
  await expect(page).toHaveURL(/\/report\?pk=BIOMD0000000012\/Model:BIOMD0000000012$/);
  await expect(page.getByTestId("report-page")).toBeVisible();
  await expect(page.getByTestId("bar-model")).toContainText("BIOMD0000000012");
  await expect(page.getByTestId("inspector-type")).toHaveText("Model");
  await page.reload();
  await expect(page.getByTestId("no-report")).toBeVisible();
});

test("pastes SBML content", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(readFileSync(REPRESSILATOR_FILE, "utf8"));
  await page.getByTestId("paste-submit").click();
  await expect(page.getByTestId("report-page")).toBeVisible();
});

test("loads a url and remembers it", async ({ page }) => {
  const url = model.url;
  await page.goto("/");
  await page.getByTestId("home-tab-url").click();
  await page.getByTestId("url-input").fill(url);
  await page.getByTestId("url-submit").click();
  await expect(page).toHaveURL(/\/report\?(.*&)?url=/);
  await expect(page.getByTestId("report-page")).toBeVisible();
  await page.reload();
  await expect(page.getByTestId("report-page")).toBeVisible();
  await page.goto("/");
  await page.getByTestId("home-tab-url").click();
  await expect(page.getByTestId("url-input")).toHaveValue(url);
});

test("an invalid url shows the error inline", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-tab-url").click();
  await page.getByTestId("url-input").fill("https://sbml4humans.de/does-not-exist.xml");
  await page.getByTestId("url-submit").click();
  await expect(page.getByTestId("error-message")).toBeVisible();
  await expect(page).toHaveURL(/\/$/);
});
