import { expect, test } from "@playwright/test";

import { openExample, query } from "./helpers";

test.describe("repressilator", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, "BIOMD0000000012");
  });

  test("selects a species, follows a referenced by link and goes back", async ({ page }) => {
    const table = page.getByTestId("table-Species");
    const row = table.locator("tbody tr[data-pk]").first();
    const pk = (await row.getAttribute("data-pk"))!;
    await row.click();
    expect(query(page, "pk")).toBe(pk);
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Species");

    await inspector.getByTestId("links-references").getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Compartment");
    const compartmentPk = query(page, "pk");

    await inspector.getByTestId("links-referenced-by").getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).not.toHaveText("Compartment");
    await page.goBack();
    expect(query(page, "pk")).toBe(compartmentPk);
    await page.goBack();
    expect(query(page, "pk")).toBe(pk);

    await inspector.getByTestId("inspector-close").click();
    expect(query(page, "pk")).toBeNull();
    await expect(page.getByTestId("inspector")).toHaveCount(0);
  });

  test("the search filters the tables", async ({ page }) => {
    const speciesRows = page.getByTestId("table-Species").locator("tbody tr[data-pk]");
    const total = await speciesRows.count();
    await page.getByTestId("search-input").fill("laci");
    await expect(page.getByTestId("rail-count-Species")).toContainText("/");
    await expect.poll(() => speciesRows.count()).toBeLessThan(total);
    expect(query(page, "q")).toBe("laci");
    await page.getByTestId("search-input").fill("zzzz-nothing");
    await expect(page.getByTestId("no-matches")).toBeVisible();
    await page.getByTestId("search-input").press("Escape");
    await expect.poll(() => speciesRows.count()).toBe(total);
  });

  test("a type can be toggled off", async ({ page }) => {
    await expect(page.getByTestId("section-Reaction")).toBeVisible();
    await page.getByTestId("rail-toggle-Reaction").click();
    await expect(page.getByTestId("section-Reaction")).toHaveCount(0);
    expect(query(page, "types")).not.toContain("Reaction");
    await page.getByTestId("rail-toggle-Reaction").click();
    await expect(page.getByTestId("section-Reaction")).toBeVisible();
    expect(query(page, "types")).toBeNull();
  });

  test("the XML toggle shows the SBML of the element", async ({ page }) => {
    await page.getByTestId("table-Species").locator("tbody tr[data-pk]").first().click();
    await page.getByTestId("inspector-xml-toggle").click();
    await expect(page.getByTestId("xml-view")).toContainText("<species");
  });
});

test("the archive dropdown switches the entry", async ({ page }) => {
  await openExample(page, "CompModels");
  const select = page.getByTestId("entry-select");
  await expect(select).toHaveValue("./models/omex_minimal.xml");
  await select.selectOption("./models/omex_comp.xml");
  await expect(page.getByTestId("model-name")).toHaveText("omex_comp");
  expect(query(page, "entry")).toBe("./models/omex_comp.xml");
});

test("the model dropdown switches to a model definition", async ({ page }) => {
  await openExample(page, "model_definitions (model_definitions.xml)");
  await page.getByTestId("model-select").selectOption("m1");
  await expect(page.getByTestId("rail-model")).toContainText("m1");
  expect(query(page, "model")).toBe("m1");
});
