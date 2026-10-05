import { expect, test } from "@playwright/test";

import { openExample, query } from "./helpers";

const EXAMPLE = "validation (validation.xml)";

test.describe("validation", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, EXAMPLE);
  });

  test("leads from the summary over the list to an element and its issues", async ({ page }) => {
    const summary = page.getByTestId("validation-summary");
    await expect(summary.getByTestId("validation-errors")).toContainText("1");
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
    expect(query(page, "pk")).toMatch(/Compartment:cell$/);

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
  });

  test("a valid model shows no summary", async ({ page }) => {
    await openExample(page, "species (species.xml)");
    await expect(page.getByTestId("validation-summary")).toHaveCount(0);
  });
});
