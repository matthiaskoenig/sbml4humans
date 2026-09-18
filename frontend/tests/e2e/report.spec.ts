import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { expect, test, type Locator } from "@playwright/test";

import { openExample, query } from "./helpers";

// read, not imported, so the typecheck of the e2e project (which has no json module support
// and no "@/" alias) does not need to know about the shape of the glossary
const glossary: { types: Record<string, { attributes: Record<string, { summary: string }> }> } =
  JSON.parse(
    readFileSync(fileURLToPath(new URL("../../src/data/glossary.json", import.meta.url)), "utf-8"),
  );

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

  test("a click on a column header sorts the rows", async ({ page }) => {
    const table = page.getByTestId("table-Species");
    const ids = () => table.locator("tbody tr[data-pk] td:first-child").allInnerTexts();
    const sortById = table.getByRole("button", { name: "id", exact: true });
    const idHeader = table.locator("thead th").first();
    await sortById.click();
    await expect(idHeader).toHaveAttribute("aria-sort", "ascending");
    expect(await ids()).toEqual(["PX", "PY", "PZ", "X", "Y", "Z"]);
    await sortById.click();
    await expect(idHeader).toHaveAttribute("aria-sort", "descending");
    expect(await ids()).toEqual(["Z", "Y", "X", "PZ", "PY", "PX"]);
    // an order other than the report order: Y has the initial amount 20, the others 0
    const amount = page.getByRole("button", { name: "initial amount", exact: true });
    const amountHeader = table.locator("thead th", { has: amount });
    await amountHeader.click();
    await expect(idHeader).toHaveAttribute("aria-sort", "none");
    await expect(amountHeader).toHaveAttribute("aria-sort", "ascending");
    expect(await ids()).toEqual(["PX", "PY", "PZ", "X", "Z", "Y"]);
  });

  test("hovering a formula shows its tooltip below it", async ({ page }) => {
    const math = page.getByTestId("table-Reaction").getByTestId("math").first();
    // a scroll hides the tooltip: scroll first and let the scroll events pass before hovering
    await math.scrollIntoViewIfNeeded();
    await page.evaluate(
      "new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))",
    );
    await math.hover();
    const tooltip = page.getByRole("tooltip");
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText("(click to copy)");
    const anchor = (await math.boundingBox())!;
    const box = (await tooltip.boundingBox())!;
    expect(box.y).toBeGreaterThanOrEqual(anchor.y + anchor.height);
    expect(box.y + box.height).toBeLessThanOrEqual(page.viewportSize()!.height);
    await page.mouse.move(0, 0);
    await expect(tooltip).toBeHidden();
  });

  test("hovering the id column header shows its tooltip and the inspector type links to the reference page", async ({
    page,
  }) => {
    const table = page.getByTestId("table-Species");
    const idHeader = table.getByRole("button", { name: "id", exact: true });
    await idHeader.hover();
    const tooltip = page.getByRole("tooltip");
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toHaveText(glossary.types.SBase!.attributes.id!.summary);
    await page.mouse.move(0, 0);
    await expect(tooltip).toBeHidden();

    await table.locator("tbody tr[data-pk]").first().click();
    await expect(page.getByTestId("inspector-type-link")).toHaveAttribute(
      "href",
      /reference\/species\//,
    );
  });
});

test("the archive dropdown switches the entry", async ({ page }) => {
  // the backend builds one report per SBML entry of an archive before it answers, so an archive
  // takes longer than a single model, and on CI the parallel workers of the other specs compete
  // for the runner's CPU while it does
  await openExample(page, "CompModels", 60_000);
  const select = page.getByRole("combobox", { name: "archive entry", exact: true });
  // the order of the archive entries follows the file system of the backend, so the start entry is not fixed
  const current = await select.inputValue();
  const target =
    current === "./models/omex_minimal.xml"
      ? "./models/omex_comp.xml"
      : "./models/omex_minimal.xml";
  const modelName = target === "./models/omex_minimal.xml" ? "omex_minimal" : "omex_comp";
  await select.selectOption(target);
  await expect(page.getByTestId("model-name")).toHaveText(modelName);
  expect(query(page, "entry")).toBe(target);
});

test("the model dropdown switches to a model definition", async ({ page }) => {
  await openExample(page, "model_definitions (model_definitions.xml)");
  await page.getByRole("combobox", { name: "model", exact: true }).selectOption("m1");
  await expect(page.getByTestId("rail-model")).toContainText("m1");
  expect(query(page, "model")).toBe("m1");
});

test.describe("a windowed table", () => {
  /** The height of a windowed row, as in ElementTable. */
  const ROW_HEIGHT = 36;
  /** The collapsed borders of the table put half of the 1 px border between two rows into
   * the box of each of them, so a row box reaches half a pixel over its visible edges. */
  const HALF_BORDER = 0.5;

  interface RowBox {
    pk: string;
    top: number;
    bottom: number;
    focused: boolean;
  }

  /** The boxes of the rendered rows, the bottom of the sticky header and the bottom of the
   * visible area of the scroller, in page coordinates. */
  function layout(
    scroller: Locator,
  ): Promise<{ headerBottom: number; viewportBottom: number; rows: RowBox[] }> {
    return scroller.evaluate((element) => ({
      headerBottom: element.querySelector("thead").getBoundingClientRect().bottom,
      viewportBottom:
        element.getBoundingClientRect().top + element.clientTop + element.clientHeight,
      rows: [...element.querySelectorAll("tbody tr[data-pk]")].map((row) => ({
        pk: row.getAttribute("data-pk"),
        top: row.getBoundingClientRect().top,
        bottom: row.getBoundingClientRect().bottom,
        focused: row === element.ownerDocument.activeElement,
      })),
    }));
  }

  test.beforeEach(async ({ page }) => {
    // creating the report of this model is CPU bound in the backend, and on CI the parallel
    // workers of the other specs compete for the runner's CPU, so this example gets the same
    // two minutes as the walk over every example in `examples-walk.spec.ts`.
    test.setTimeout(150_000);
    // 249 parameters: the smallest example with more than 200 rows of one type
    await openExample(page, "dex_body (dex_body_flat.xml)", 120_000);
    const scroller = page.getByTestId("table-Parameter");
    await scroller.scrollIntoViewIfNeeded();
    await scroller.evaluate((element, top) => (element.scrollTop = top), 100 * ROW_HEIGHT);
    // the window follows the scroll one animation frame later
    await expect
      .poll(() => scroller.getByTestId("spacer-before").evaluate((row) => row.offsetHeight))
      .toBe(95 * ROW_HEIGHT);
  });

  test("renders the rows around the scroll position", async ({ page }) => {
    const scroller = page.getByTestId("table-Parameter");
    // the 15 rows of the viewport from row 100 on, with 5 rows of overscan on each side
    await expect(scroller.locator("tbody tr[data-pk]")).toHaveCount(25);
    const { headerBottom, rows } = await layout(scroller);
    expect(rows.slice(1).map((row, i) => row.bottom - rows[i]!.bottom)).toEqual(
      Array(24).fill(ROW_HEIGHT),
    );
    // row 100 lies right below the sticky header
    expect(Math.abs(rows[5]!.bottom - ROW_HEIGHT - headerBottom)).toBeLessThanOrEqual(HALF_BORDER);
    await expect(scroller.locator("tbody tr[data-pk]").nth(5)).toBeInViewport();
  });

  test("keeps the row the arrow keys move to inside the viewport", async ({ page }) => {
    const scroller = page.getByTestId("table-Parameter");
    const focused = scroller.locator("tbody tr[data-pk]:focus");

    /** Presses the key, checks that the focus moves to the neighbouring row and that the row
     * lies fully inside the viewport and below the sticky header, and returns the box the
     * row had before. */
    async function press(key: "ArrowDown" | "ArrowUp"): Promise<RowBox> {
      const before = await layout(scroller);
      const index = before.rows.findIndex((row) => row.focused);
      const next = before.rows[index + (key === "ArrowDown" ? 1 : -1)]!;
      await page.keyboard.press(key);
      await expect(focused).toHaveAttribute("data-pk", next.pk);
      const after = await layout(scroller);
      const row = after.rows.find((candidate) => candidate.focused)!;
      expect(row.top).toBeGreaterThanOrEqual(after.headerBottom - HALF_BORDER);
      expect(row.bottom).toBeLessThanOrEqual(after.viewportBottom + HALF_BORDER);
      return next;
    }

    // ArrowDown from the last row in view moves the focus past the bottom edge
    const start = await layout(scroller);
    const lastInView = start.rows.filter((row) => row.bottom <= start.viewportBottom).at(-1)!;
    await scroller.locator(`tr[data-pk="${lastInView.pk}"]`).focus();
    expect((await press("ArrowDown")).bottom).toBeGreaterThan(start.viewportBottom);
    await press("ArrowDown");
    await press("ArrowDown");

    // ArrowUp from the first row below the sticky header moves the focus under the header
    const scrolled = await layout(scroller);
    const firstInView = scrolled.rows.find(
      (row) => row.top >= scrolled.headerBottom - HALF_BORDER,
    )!;
    await scroller.locator(`tr[data-pk="${firstInView.pk}"]`).focus();
    expect((await press("ArrowUp")).top).toBeLessThan(scrolled.headerBottom);
    await press("ArrowUp");
    await press("ArrowUp");
  });
});
