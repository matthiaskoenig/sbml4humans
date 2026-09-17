import { expect, test } from "@playwright/test";

test("a page opened from a report receives only the origin as its referrer", async ({ page }) => {
  await page.goto("/examples/BIOMD0000000012?q=abc");
  await expect(page.getByTestId("report-page")).toBeVisible();

  // a full navigation, as a link opened in a new tab does, not a navigation of the router; the
  // expressions are strings, since the end to end tests are type checked without the DOM types
  await page.evaluate("location.assign('/examples')");
  await expect(page.getByTestId("examples-page")).toBeVisible();

  const origin = new URL(page.url()).origin;
  expect(await page.evaluate("document.referrer")).toBe(`${origin}/`);
});
