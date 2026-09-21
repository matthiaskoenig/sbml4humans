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

test.describe("the report page of a phone", () => {
  test("opens with the tables and no element selected", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    await expect(page.getByTestId("tables")).toBeVisible();
    await expect(page.getByTestId("inspector")).toHaveCount(0);
    expect(new URL(page.url()).searchParams.get("pk")).toBeNull();
  });

  test("shows the inspector in place of the tables and returns to them", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    const tables = page.getByTestId("tables");
    const row = page.getByTestId("table-Reaction").locator("tbody tr[data-pk]").first();
    await row.scrollIntoViewIfNeeded();
    const scrolled = await tables.evaluate((element) => element.scrollTop);
    expect(scrolled).toBeGreaterThan(0);
    await row.click();

    const inspector = page.getByTestId("inspector");
    await expect(inspector).toBeVisible();
    await expect(tables).toBeHidden();
    await expect(page.getByTestId("split-handle")).toHaveCount(0);
    await expect(page.getByTestId("inspector-close")).toHaveCount(0);
    // the inspector has the width of the window
    const box = await inspector.boundingBox();
    expect(box!.width).toBe(page.viewportSize()!.width);
    await expectNoOverflow(page);

    // the button of the header returns to the tables where the reader left them
    await page.getByTestId("inspector-back").click();
    await expect(tables).toBeVisible();
    await expect(inspector).toHaveCount(0);
    expect(await tables.evaluate((element) => element.scrollTop)).toBe(scrolled);
  });

  test("returns to the tables with the back button of the browser", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    await page.getByTestId("table-Species").locator("tbody tr[data-pk]").first().click();
    await expect(page.getByTestId("inspector")).toBeVisible();
    await page.goBack();
    await expect(page.getByTestId("tables")).toBeVisible();
    await expect(page.getByTestId("inspector")).toHaveCount(0);
  });

  test("opens the model from the type bar", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    await page.getByTestId("bar-model").click();
    await expect(page.getByTestId("inspector-id")).toHaveText("BIOMD0000000012");
  });
});

test.describe("the tables of a phone", () => {
  test("keep the id of a row in view while the table scrolls sideways", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    const table = page.getByTestId("table-Parameter");
    const idCell = table.locator("tbody tr[data-pk]").first().locator("td").first();
    const idHeader = table.locator("thead th").first();
    const before = await idCell.boundingBox();
    const scrollLeft = await table.evaluate((element) => {
      element.scrollLeft = 300;
      return element.scrollLeft;
    });
    expect(scrollLeft).toBeGreaterThan(0);
    // pinned a pixel beyond the edge of the scroll, see `pinned` of the table
    const after = await idCell.boundingBox();
    expect(after!.x).toBe(before!.x - 1);
    expect((await idHeader.boundingBox())!.x).toBe(before!.x - 1);
    // the pinned column leaves the other columns more than half of the table
    const box = await table.boundingBox();
    expect(after!.width).toBeLessThanOrEqual(box!.width / 2);
  });

  test("cut a long id off before it takes the width of the other columns", async ({ page }) => {
    await openExample(page, "e_coli_core (e_coli_core.xml.gz)");
    const table = page.getByTestId("table-Reaction");
    const idCell = table.locator("tbody tr[data-pk]").first().locator("td").first();
    const box = await table.boundingBox();
    expect((await idCell.boundingBox())!.width).toBeLessThanOrEqual(box!.width / 2);
  });
});

test.describe("the type bar of a phone", () => {
  test("holds the types behind one button which says how many are shown", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    const toggle = page.getByTestId("type-bar-toggle");
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(toggle).toContainText("6 / 6");
    await expect(page.getByTestId("bar-toggle-Species")).toBeHidden();
    // the document and the model stay in reach
    await expect(page.getByTestId("bar-document")).toBeVisible();
    await expect(page.getByTestId("bar-model")).toBeVisible();

    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await page.getByTestId("bar-toggle-Species").uncheck();
    await expect(toggle).toContainText("5 / 6");
    await expect(page.getByTestId("section-Species")).toHaveCount(0);
    await expectNoOverflow(page);
  });

  test("closes when a type is scrolled to", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    await page.getByTestId("type-bar-toggle").click();
    await page.getByTestId("bar-type-Reaction").getByRole("button").click();
    await expect(page.getByTestId("bar-toggle-Species")).toBeHidden();
    await expect(page.getByTestId("section-Reaction")).toBeInViewport();
  });

  test("gives way to the inspector", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    await page.getByTestId("bar-model").click();
    await expect(page.getByTestId("inspector")).toBeVisible();
    await expect(page.getByTestId("type-bar")).toBeHidden();
  });
});

test("the report page of a phone leaves the footer to the other pages", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-footer")).toBeVisible();
  await openExample(page, REPRESSILATOR);
  await expect(page.getByTestId("app-footer")).toBeHidden();
});

test.describe("the help dialog of a phone", () => {
  test("fills the window", async ({ page }) => {
    await openExample(page, REPRESSILATOR);
    await page.getByTestId("section-Species").getByTestId("help-button").first().click();
    const dialog = page.getByTestId("help-dialog");
    await expect(dialog).toBeVisible();
    const box = await dialog.boundingBox();
    const viewport = page.viewportSize()!;
    expect(box!.width).toBe(viewport.width);
    expect(box!.height).toBe(viewport.height);
    await expectNoOverflow(page);
  });
});

test("the examples page of a phone stacks the heading and the filter", async ({ page }) => {
  await page.goto("/examples");
  const heading = await page.getByRole("heading", { name: "Examples" }).boundingBox();
  const filter = await page.getByTestId("examples-filter").boundingBox();
  expect(filter!.y).toBeGreaterThan(heading!.y + heading!.height - 1);
  expect(filter!.width).toBeGreaterThan(page.viewportSize()!.width - 40);
});

test("a tap leaves no tooltip behind", async ({ page }) => {
  await openExample(page, REPRESSILATOR);
  // the button which sorts a column explains itself on hover, and a finger does not hover
  await page.getByTestId("table-Species").getByTestId("sort-button").first().tap();
  await expect(page.getByTestId("table-Species").locator("th[aria-sort=ascending]")).toHaveCount(1);
  await expect(page.locator("#app-tooltip")).toBeHidden();
});
