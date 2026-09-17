import { expect, test } from "@playwright/test";

test("the examples page lists the examples and opens one", async ({ page }) => {
  await page.goto("/examples");
  const cards = page.getByTestId("example-card");
  await expect(cards.first()).toBeVisible();
  expect(await cards.count()).toBeGreaterThan(50);
  await page.getByTestId("examples-filter").fill("repressilator");
  await expect(cards).toHaveCount(2);
  await cards.first().click();
  await expect(page).toHaveURL(/\/examples\/BIOMD0000000012/);
  await expect(page.getByTestId("report-page")).toBeVisible();
});

test("an unknown example shows the api error", async ({ page }) => {
  await page.goto("/examples/nope");
  await expect(page.getByTestId("error-message")).toHaveText(
    "example for id does not exist 'nope'",
  );
  await page.getByTestId("error-traceback-toggle").click();
  await expect(page.getByTestId("error-traceback")).toContainText("Traceback");
});
