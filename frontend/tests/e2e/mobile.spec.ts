import { expect, test, type Page } from "@playwright/test";

import { openExample } from "./helpers";

const REPRESSILATOR = "BIOMD0000000012 (BIOMD0000000012_urn.xml)";

/** The page never scrolls sideways on a phone: what is wider than the window, a table, scrolls
 * inside a box of its own. */
async function expectNoOverflow(page: Page): Promise<void> {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
}

test.describe("the pages fit a phone", () => {
  test("the home page does not scroll sideways", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("app-bar")).toBeVisible();
    await expectNoOverflow(page);
  });

  test("the examples page does not scroll sideways", async ({ page }) => {
    await page.goto("/examples");
    await expect(page.getByTestId("examples-grid")).toBeVisible();
    await expectNoOverflow(page);
  });

  test("the report page does not scroll sideways", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    await expectNoOverflow(page);
    // the search has a row of its own, as wide as the window allows
    const search = await page.getByTestId("search-input").boundingBox();
    const viewport = page.viewportSize();
    expect(search!.x + search!.width).toBeLessThanOrEqual(viewport!.width);
  });
});

test.describe("the menu of the app bar", () => {
  test("holds the links of the bar behind one button", async ({ page }) => {
    await page.goto("/");
    const docs = page.getByTestId("app-bar-docs");
    await expect(docs).toBeHidden();
    const menu = page.getByTestId("app-bar-menu");
    await expect(menu).toHaveAttribute("aria-expanded", "false");
    await menu.click();
    await expect(menu).toHaveAttribute("aria-expanded", "true");
    await expect(docs).toBeVisible();
    await expect(page.getByTestId("app-bar-feedback")).toBeVisible();
    await expectNoOverflow(page);
    // Escape closes the menu again
    await page.keyboard.press("Escape");
    await expect(docs).toBeHidden();
  });

  test("closes when a link of it opens a page", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("app-bar-menu").click();
    await page.getByTestId("app-bar-examples").click();
    await expect(page.getByTestId("examples-page")).toBeVisible();
    await expect(page.getByTestId("app-bar-docs")).toBeHidden();
  });
});
