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
  await page.goto(
    `/examples/${REPRESSILATOR}?pk=${encodeURIComponent("BIOMD0000000012/Species:X")}`,
  );
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

test("the code of the equations in tabs, kept in the url", async ({ page }) => {
  await page.goto(`/examples/${REPRESSILATOR}?view=equations`);
  await expectReport(page);
  const view = page.getByTestId("equations-view");
  // the math reads from the definitions to the system
  const sections = view.locator("section[data-testid^=equations-]");
  await expect(sections).toHaveCount(3);
  expect(
    await sections.evaluateAll((all) => all.map((s) => s.getAttribute("data-testid"))),
  ).toEqual(["equations-odeAssignments", "equations-reactionRates", "equations-odeSystem"]);

  await page.getByTestId("equations-tab-julia").click();
  await expect.poll(() => query(page, "code")).toBe("julia");
  await expect(page.getByTestId("equations-code-text")).toContainText("function f!(dx, x, p, t)");
  await expect(page.getByTestId("equations-code-filename")).toHaveText("BIOMD0000000012.jl");
  await expect(view.getByTestId("equation-row")).toHaveCount(0);
  // a reload keeps the tab
  await page.reload();
  await expectReport(page);
  await expect(page.getByTestId("equations-tab-julia")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("equations-code-text")).toContainText("function f!(dx, x, p, t)");
  // the arrow keys move between the tabs
  await page.getByTestId("equations-tab-julia").press("ArrowRight");
  await expect.poll(() => query(page, "code")).toBe("r");
  await expect(page.getByTestId("equations-tab-r")).toBeFocused();
  await page.getByTestId("equations-tab-math").click();
  await expect.poll(() => query(page, "code")).toBeNull();
  await expect(view.getByTestId("equation-row").first()).toBeVisible();
});

test("the code downloads and copies the ODE system without the simulator", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto(`/examples/${REPRESSILATOR}?view=equations&code=python`);
  await expectReport(page);
  await expect(page.getByTestId("equations-code-text")).toContainText("def f_dxdt(");
  const downloading = page.waitForEvent("download");
  await page.getByTestId("equations-code-download").click();
  const download = await downloading;
  expect(download.suggestedFilename()).toBe("BIOMD0000000012.py");
  const code = readFileSync((await download.path())!, "utf8");
  expect(code).toContain("def f_dxdt(");
  expect(code).not.toContain("def simulate(");
  await page.getByTestId("equations-code-copy").click();
  await expect(page.getByTestId("equations-code-copy")).toHaveText("Copied");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(code);
  await expect(page.getByTestId("equations-code-sbmlode")).toHaveAttribute(
    "href",
    "https://matthiaskoenig.github.io/sbmlode/formats/",
  );
});

test("a concentration in a compartment whose size changes is diluted", async ({ page }) => {
  await openExample(page, "variable_compartment (variable_compartment.xml)");
  await page.getByTestId("view-equations").click();
  const view = page.getByTestId("equations-view");
  const s1 = view.locator('[data-equation-of="variable_compartment/Species:S1"]');
  // the ODE of S1 ends with the rate of the size of Vc, a link to the compartment
  await expect(s1.locator('[data-pk="variable_compartment/Compartment:Vc"]').last()).toBeVisible();
  // the rate of the size of Va, which has an assignment rule, is an assignment
  await expect(
    view
      .getByTestId("equations-odeAssignments")
      .locator('[data-equation-of="variable_compartment/Compartment:Va"]'),
  ).toHaveCount(2);
  await expect(view.getByTestId("equation-origin").filter({ hasText: "size rate" })).toHaveCount(1);
});

test("a model with an algebraic rule names it as unsupported", async ({ page }) => {
  await openExample(page, "algebraic_rule (algebraic_rule.xml)");
  await page.getByTestId("view-equations").click();
  const notice = page.getByTestId("equations-unsupported");
  await expect(notice).toContainText("algebraic rule");
  // code of a system without its algebraic rule would simulate another model
  await page.getByTestId("equations-tab-python").click();
  await expect(page.getByTestId("equations-code-error")).toContainText("algebraic rule");
  // the notice stays above the code
  await expect(notice).toBeVisible();
});
