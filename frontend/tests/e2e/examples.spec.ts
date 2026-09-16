import { expect, test } from "@playwright/test";

import { openExample } from "./helpers";

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

test("every example renders its sections", async ({ page, request }) => {
  const response = await request.get("http://localhost:1444/api/examples");
  const { examples } = (await response.json()) as { examples: { id: string }[] };
  test.setTimeout(examples.length * 15_000);
  for (const example of examples) {
    await openExample(page, example.id);
    await expect(page.getByTestId("type-rail")).toBeVisible();
    const sections = await page.locator("[data-testid^=section-]").count();
    // a model without any element renders the empty state instead of the sections
    if (sections === 0) await expect(page.getByTestId("no-matches"), example.id).toBeVisible();
    await expect(page.getByTestId("error-state"), example.id).toHaveCount(0);
  }
});

test("an unknown example shows the api error", async ({ page }) => {
  await page.goto("/examples/nope");
  await expect(page.getByTestId("error-message")).toHaveText(
    "example for id does not exist 'nope'",
  );
  await page.getByTestId("error-traceback-toggle").click();
  await expect(page.getByTestId("error-traceback")).toContainText("Traceback");
});
