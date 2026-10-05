import { expect, test } from "@playwright/test";

import { openExample, query } from "./helpers";

const EXAMPLE = "validation (validation.xml)";

/** A comp document whose main model expands to `n` submodels on each of `depth` levels. */
function fanOut(depth: number, n: number): string {
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
    `<model id="m">${submodels(`d${depth - 1}`)}</model>` +
    `<comp:listOfModelDefinitions>${definitions}</comp:listOfModelDefinitions></sbml>`
  );
}

test.describe("validation", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, EXAMPLE);
  });

  test("leads from the summary over the list to an element and its issues", async ({ page }) => {
    const summary = page.getByTestId("validation-summary");
    await expect(summary.getByTestId("validation-errors")).toHaveText("1 error");
    await expect(summary.getByTestId("validation-errors")).toHaveAccessibleName("1 error");
    await expect(summary.getByTestId("validation-warnings")).toBeVisible();

    await summary.getByTestId("validation-errors").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("SBMLDocument");
    const groups = inspector.getByTestId("validation-list").getByTestId("validation-group");
    await expect(groups.first()).toContainText("10601");

    const compartment = groups.filter({ hasText: "10712" });
    await compartment.locator("summary").click();
    await compartment.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Compartment");
    await expect(inspector.getByTestId("inspector-validation")).toContainText("10712");
    await expect.poll(() => query(page, "pk")).toMatch(/Compartment:cell$/);

    // back returns to the list of the document
    await page.goBack();
    await expect(inspector.getByTestId("validation-list")).toBeVisible();
  });

  test("marks the rows and the types with issues", async ({ page }) => {
    await expect(
      page.locator('tbody tr[data-pk$="Parameter:k1"]').getByTestId("row-issue"),
    ).toBeVisible();
    await expect(
      page.locator('tbody tr[data-pk$="Species:A"]').getByTestId("row-issue"),
    ).toHaveCount(0);
    await expect(
      page.getByTestId("bar-type-Parameter").getByTestId("severity-warning"),
    ).toBeVisible();
    // the reaction R1 has no issue of its own, the issue of its kinetic law marks its row
    await expect(
      page.locator('tbody tr[data-pk$="Reaction:R1"]').getByTestId("row-issue"),
    ).toBeVisible();
    await expect(
      page.getByTestId("bar-type-Reaction").getByTestId("severity-warning"),
    ).toBeVisible();
    // the error of the example is an issue of the model, whose entry of the type bar is its row
    await expect(page.getByTestId("bar-model").getByTestId("severity-error")).toBeVisible();
    await expect(page.getByTestId("bar-document").getByTestId("bar-issue-document")).toHaveCount(0);
  });

  test("a document beyond the budget of submodel instances says it was not validated", async ({
    page,
  }) => {
    await page.goto("/");
    await page.getByTestId("home-tab-paste").click();
    await page.getByTestId("paste-input").fill(fanOut(5, 10));
    await page.getByTestId("paste-submit").click();
    await expect(page.getByTestId("report-page")).toBeVisible();

    const skipped = page.getByTestId("validation-summary").getByTestId("validation-skipped");
    await expect(skipped).toHaveText("not validated");
    await expect(page.getByTestId("validation-errors")).toHaveCount(0);
    await skipped.click();
    const list = page.getByTestId("inspector").getByTestId("validation-list");
    await expect(list.getByTestId("validation-skipped")).toBeVisible();
    await expect(list.getByTestId("no-validation-issues")).toHaveCount(0);
  });

  test("a valid model shows no summary", async ({ page }) => {
    await openExample(page, "species (species.xml)");
    await expect(page.getByTestId("validation-summary")).toHaveCount(0);
  });
});
