import { readFileSync } from "node:fs";

import { expect, test } from "@playwright/test";

import { expectReport, openExample, query, search } from "./helpers";

const REPRESSILATOR = "BIOMD0000000012";

test("the equations of a model, linked to the inspector", async ({ page }) => {
  await openExample(page, REPRESSILATOR);
  await page.getByTestId("view-equations").click();
  await expect.poll(() => query(page, "view")).toBe("equations");
  const view = page.getByTestId("equations-view");
  await expect(view.getByTestId("equations-odeSystem").getByTestId("equations-count")).toHaveText(
    "6",
  );
  await expect(
    view.getByTestId("equations-reactionRates").getByTestId("equations-count"),
  ).toHaveText("12");
  await expect(
    view.getByTestId("equations-odeAssignments").getByTestId("equations-count"),
  ).toHaveText("9");
  // the types filter the tables, they are no entries of the bar next to the equations
  await expect(page.getByTestId("bar-type-Species")).toHaveCount(0);

  // a symbol of an equation opens its element in the inspector
  await view.locator('[data-pk="BIOMD0000000012/Reaction:Reaction1"]').first().click();
  await expect.poll(() => query(page, "pk")).toBe("BIOMD0000000012/Reaction:Reaction1");
  await expect(page.getByTestId("inspector-id")).toHaveText("Reaction1");
  await expect(view.locator('[data-equation-of="BIOMD0000000012/Reaction:Reaction1"]')).toHaveClass(
    /bg-selected/,
  );

  // a reload keeps the view and the selection
  await page.reload();
  await expectReport(page);
  await expect(page.getByTestId("equations-view")).toBeVisible();

  // a search filters the tables, so it shows them
  await search(page, "PX");
  await expect(page.getByTestId("equations-view")).toHaveCount(0);
  expect(query(page, "view")).toBeNull();
});

test("the inspector of a species shows its equation and opens it in the view", async ({ page }) => {
  await page.goto(`/examples/${REPRESSILATOR}?pk=${encodeURIComponent("BIOMD0000000012/Species:X")}`);
  await expectReport(page);
  const block = page.getByTestId("equation-block");
  await expect(block.getByTestId("equation-row")).toHaveCount(1);
  await block.getByTestId("equation-block-show").click();
  await expect.poll(() => query(page, "view")).toBe("equations");
  await expect(
    page.getByTestId("equations-view").locator('[data-equation-of="BIOMD0000000012/Species:X"]'),
  ).toHaveClass(/bg-selected/);
  await expect(block.getByTestId("equation-block-show")).toHaveCount(0);
});

test("the equations download as python code", async ({ page }) => {
  await page.goto(`/examples/${REPRESSILATOR}?view=equations`);
  await expectReport(page);
  const downloading = page.waitForEvent("download");
  await page.getByTestId("ode-download-python").click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("BIOMD0000000012.py");
  const code = readFileSync((await download.path())!, "utf8");
  expect(code).toContain("def f_dxdt(");
});

test("a model with an algebraic rule names it as unsupported", async ({ page }) => {
  await openExample(page, "algebraic_rule (algebraic_rule.xml)");
  await page.getByTestId("view-equations").click();
  const notice = page.getByTestId("equations-unsupported");
  await expect(notice).toContainText("algebraic rule");
  // code of a system without its algebraic rule would simulate another model
  await page.getByTestId("ode-download-python").click();
  await expect(page.getByTestId("ode-download-error")).toContainText("algebraic rule");
});
