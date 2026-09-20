import { expect, test, type Page } from "@playwright/test";

import { attributeRow, openExample, query } from "./helpers";

/** The repressilator, the model every test of this file opens: small enough to load quickly and
 * rich enough to carry a species, a compartment and a reaction with the attributes the dialog
 * explains. */
const REPRESSILATOR = "BIOMD0000000012";

/** Selects the first row of the species table and returns the inspector, open on it. */
async function selectFirstSpecies(page: Page) {
  await page.getByTestId("table-Species").locator("tbody tr[data-pk]").first().click();
  return page.getByTestId("inspector");
}

test.describe("the help dialog", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, REPRESSILATOR);
  });

  test("opens from a label of the inspector and writes the entry into the url", async ({
    page,
  }) => {
    const inspector = await selectFirstSpecies(page);
    await attributeRow(inspector, "initialAmount").getByTestId("help-label").click();

    const dialog = page.getByTestId("help-dialog");
    await expect(dialog).toBeVisible();
    await expect(page.getByTestId("help-title")).toHaveText("initialAmount");
    await expect.poll(() => query(page, "help")).toBe("types/Species/initialAmount");
    await expect(page.getByTestId("help-required-badge")).toHaveText("optional");
    await expect(page.getByTestId("help-technical")).toContainText("double");
    await expect(page.getByTestId("help-rule").first()).toBeVisible();
  });

  test("walks between entries and back through the browser history", async ({ page }) => {
    const inspector = await selectFirstSpecies(page);
    const pk = query(page, "pk");
    await attributeRow(inspector, "initialAmount").getByTestId("help-label").click();
    await expect.poll(() => query(page, "help")).toBe("types/Species/initialAmount");

    // the breadcrumb of the attribute leads to its owner, the type
    await page.getByTestId("help-owner").click();
    await expect(page.getByTestId("help-title")).toHaveText("Species");
    await expect.poll(() => query(page, "help")).toBe("types/Species");

    // the attributes table of the type leads to one of its attributes
    await page
      .getByTestId("help-attribute-row")
      .filter({ hasText: "compartment" })
      .getByRole("link")
      .click();
    await expect(page.getByTestId("help-title")).toHaveText("compartment");
    await expect.poll(() => query(page, "help")).toBe("types/Species/compartment");

    // every entry opened a route of its own, so the back button walks through them in place
    await page.goBack();
    await expect.poll(() => query(page, "help")).toBe("types/Species");
    await expect(page.getByTestId("help-dialog")).toBeVisible();
    await page.goBack();
    await expect.poll(() => query(page, "help")).toBe("types/Species/initialAmount");
    await expect(page.getByTestId("help-dialog")).toBeVisible();

    // the report itself is one step further back, with the species still selected
    await page.goBack();
    await expect.poll(() => query(page, "help")).toBeNull();
    await expect(page.getByTestId("help-dialog")).toBeHidden();
    expect(query(page, "pk")).toBe(pk);
  });

  test("escape closes the dialog and returns the focus to the label which opened it", async ({
    page,
  }) => {
    const inspector = await selectFirstSpecies(page);
    const label = attributeRow(inspector, "initialAmount").getByTestId("help-label");
    await label.click();
    await expect(page.getByTestId("help-dialog")).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(page.getByTestId("help-dialog")).toBeHidden();
    await expect.poll(() => query(page, "help")).toBeNull();
    await expect(label).toBeFocused();
  });

  test("the close button and the backdrop close the dialog, a text selection ending on it does not", async ({
    page,
  }) => {
    const inspector = await selectFirstSpecies(page);
    const label = attributeRow(inspector, "initialAmount").getByTestId("help-label");
    const dialog = page.getByTestId("help-dialog");

    await label.click();
    await expect(dialog).toBeVisible();
    await page.getByTestId("help-close").click();
    await expect(dialog).toBeHidden();
    await expect.poll(() => query(page, "help")).toBeNull();

    await label.click();
    await expect(dialog).toBeVisible();
    const box = (await dialog.boundingBox())!;
    // a point halfway between the edge of the viewport and the edge of the dialog's own box is
    // always the backdrop, whatever the viewport happens to be
    await page.mouse.click(box.x / 2, box.y / 2);
    await expect(dialog).toBeHidden();
    await expect.poll(() => query(page, "help")).toBeNull();

    await label.click();
    await expect(dialog).toBeVisible();
    const summaryBox = (await page.getByTestId("help-summary").boundingBox())!;
    await page.mouse.move(
      summaryBox.x + summaryBox.width / 2,
      summaryBox.y + summaryBox.height / 2,
    );
    await page.mouse.down();
    await page.mouse.move(box.x / 2, box.y / 2);
    await page.mouse.up();
    await expect(dialog).toBeVisible();
    await expect.poll(() => query(page, "help")).toBe("types/Species/initialAmount");
  });

  // the browser hands the focus back to the label which opened the dialog, and a tooltip on it
  // would stand on the report while the pointer rests where the dialog was
  test("leaves no tooltip on the label it returns the focus to, and shows one for the keyboard", async ({
    page,
  }) => {
    const inspector = await selectFirstSpecies(page);
    const label = attributeRow(inspector, "initialAmount").getByTestId("help-label");
    const tooltip = page.locator("#app-tooltip");

    await label.click();
    await expect(page.getByTestId("help-dialog")).toBeVisible();
    await page.getByTestId("help-close").click();
    await expect(page.getByTestId("help-dialog")).toBeHidden();
    await expect(label).toBeFocused();
    await expect(tooltip).toBeHidden();

    // a reader who reaches the label with Tab is shown its sentence as before: the focus leaves
    // it and comes back, so that the browser judges the focus as one of the keyboard
    await label.focus();
    await page.keyboard.press("Shift+Tab");
    await page.keyboard.press("Tab");
    await expect(label).toBeFocused();
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText("the amount of the species when the simulation starts");
  });

  // the cell of a label truncates it, which clips whatever is painted outside its box: an
  // outline around the label would be cut at the left edge of the column, and one inside it is
  // whole wherever the label stands
  test("the focus outline of a label is painted inside the label", async ({ page }) => {
    const inspector = await selectFirstSpecies(page);
    const label = attributeRow(inspector, "initialAmount").getByTestId("help-label");
    await label.focus();
    await page.keyboard.press("Shift+Tab");
    await page.keyboard.press("Tab");
    await expect(label).toBeFocused();
    await expect(label).toHaveCSS("outline-style", "solid");
    await expect(label).toHaveCSS("outline-offset", "-2px");
  });

  test("the header of a column still sorts, and its help opens no sort of its own", async ({
    page,
  }) => {
    const table = page.getByTestId("table-Species");
    const header = table.locator("thead th", {
      has: page.getByRole("button", { name: "initialAmount", exact: true }),
    });

    await header.getByTestId("sort-button").click();
    await expect(header).toHaveAttribute("aria-sort", "ascending");
    expect(query(page, "help")).toBeNull();

    // the icon is transparent until the header is hovered or carries the focus, as a user would
    // find it, and only then is it the target a click reaches
    await header.hover();
    const help = header.getByTestId("help-button");
    await expect(help).toHaveCSS("opacity", "1");
    await help.click();

    await expect(page.getByTestId("help-dialog")).toBeVisible();
    await expect.poll(() => query(page, "help")).toBe("types/Species/initialAmount");
    await expect(header).toHaveAttribute("aria-sort", "ascending");
  });

  // the icon takes no width from the column: it stands a step after the name of its own column,
  // in the padding which parts that name from the name of the next one, and the icon of the last
  // column stands inside the cell, where it cannot make the table scroll
  test("the help of a header stands after its name and reaches neither the next column nor past the table", async ({
    page,
  }) => {
    const table = page.getByTestId("table-Species");
    const headers = table.locator("thead th");
    const header = table.locator("thead th", {
      has: page.getByRole("button", { name: "compartment", exact: true }),
    });
    await header.hover();
    // the button of the header, which carries the name and the arrows
    const name = (await header.getByTestId("sort-button").boundingBox())!;
    const help = (await header.getByTestId("help-button").boundingBox())!;
    const next = (await header.locator("xpath=following-sibling::th[1]//div").boundingBox())!;

    expect(help.x).toBeGreaterThanOrEqual(name.x + name.width);
    expect(help.x + help.width).toBeLessThanOrEqual(next.x);

    // a column whose cell is much wider than its header keeps the icon next to the name and not
    // at the far edge of the cell, where it would stand next to the name of the column after it
    const wide = page.getByTestId("table-Parameter").locator("thead th", {
      has: page.getByRole("button", { name: "name", exact: true }),
    });
    await wide.hover();
    const wideName = (await wide.getByTestId("sort-button").boundingBox())!;
    const wideHelp = (await wide.getByTestId("help-button").boundingBox())!;
    expect((await wide.boundingBox())!.width).toBeGreaterThan(wideName.width + 60);
    expect(wideHelp.x - (wideName.x + wideName.width)).toBeLessThanOrEqual(8);

    const last = headers.last();
    await last.hover();
    const lastHelp = (await last.getByTestId("help-button").boundingBox())!;
    const tableBox = (await table.locator("table").boundingBox())!;
    expect(lastHelp.x + lastHelp.width).toBeLessThanOrEqual(tableBox.x + tableBox.width);

    // the square around the icon is the target of a click which lands next to it, and that click
    // explains the column instead of sorting it
    await header.hover();
    await page.mouse.click(help.x - 5, help.y + help.height / 2 + 5);
    await expect(page.getByTestId("help-dialog")).toBeVisible();
    await expect.poll(() => query(page, "help")).toBe("types/Species/compartment");
    await expect(header).toHaveAttribute("aria-sort", "none");
  });

  test("the type badge and a link of the prose open their own entry", async ({ page }) => {
    const inspector = await selectFirstSpecies(page);
    await attributeRow(inspector, "initialAmount").getByTestId("help-label").click();
    await expect(page.getByTestId("help-dialog")).toBeVisible();

    await page.getByTestId("help-type-badge").click();
    await expect(page.getByTestId("help-title")).toHaveText("double");
    await expect.poll(() => query(page, "help")).toBe("datatypes/double");

    await page.goto(`/examples/${encodeURIComponent(REPRESSILATOR)}?help=types/Species`);
    await expect(page.getByTestId("report-page")).toBeVisible();
    const link = page.getByTestId("help-markdown").locator("a[data-help-key]").first();
    const key = await link.getAttribute("data-help-key");
    await link.click();
    await expect.poll(() => query(page, "help")).toBe(key);
    await expect(page.getByTestId("help-title")).toBeVisible();
  });

  test("a deep link opens the dialog on that entry, an unknown or malformed one opens none", async ({
    page,
  }) => {
    const errors: string[] = [];
    const consoleErrors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    await page.goto(`/examples/${encodeURIComponent(REPRESSILATOR)}?help=types/Compartment/units`);
    await expect(page.getByTestId("report-page")).toBeVisible();
    await expect(page.getByTestId("help-dialog")).toBeVisible();
    await expect(page.getByTestId("help-title")).toHaveText("units");
    // the title above shows already from the eager glossary; the rules come with the details,
    // behind their own dynamic import, so the section itself is what a test has to wait for
    // before counting its rows. The exact number of rules is too brittle a thing to pin, that
    // there is more than a couple of them is enough to show the list renders
    await expect(page.getByTestId("help-rules")).toBeVisible();
    expect(await page.getByTestId("help-rule").count()).toBeGreaterThanOrEqual(3);

    await page.goto(`/examples/${encodeURIComponent(REPRESSILATOR)}?help=types/Nope`);
    await expect(page.getByTestId("report-page")).toBeVisible();
    await expect(page.getByTestId("help-dialog")).toBeHidden();
    await expect.poll(() => query(page, "help")).toBeNull();

    await page.goto(`/examples/${encodeURIComponent(REPRESSILATOR)}?help=foo/bar`);
    await expect(page.getByTestId("report-page")).toBeVisible();
    await expect(page.getByTestId("help-dialog")).toBeHidden();
    await expect.poll(() => query(page, "help")).toBeNull();

    expect(errors).toEqual([]);
    expect(consoleErrors).toEqual([]);
  });

  test("the long description and the markdown renderer load only with the first dialog", async ({
    page,
  }) => {
    // the dev server serves every module by its source path, so a request is matched by the file
    // name it carries rather than by a bundled chunk name, which only the production build has;
    // that build is checked separately, by the list of files `vite build` writes, not by this
    // test. The url of the details is a module of a few bytes which every report page holds from
    // its first render, so the json itself is told from it by the kind of request it is: the
    // loader fetches it, the module is a script the browser imports.
    const requests: { url: string; kind: string }[] = [];
    page.on("request", (request) =>
      requests.push({ url: request.url(), kind: request.resourceType() }),
    );
    const fetchedDetails = () =>
      requests.some(({ url, kind }) => url.includes("glossary-details") && kind === "fetch");

    await page.goto(`/examples/${encodeURIComponent(REPRESSILATOR)}`);
    await expect(page.getByTestId("report-page")).toBeVisible();
    const inspector = await selectFirstSpecies(page);
    expect(fetchedDetails()).toBe(false);
    expect(requests.some(({ url }) => url.includes("HelpMarkdown"))).toBe(false);
    expect(requests.some(({ url }) => url.includes("markdown-it"))).toBe(false);

    await attributeRow(inspector, "initialAmount").getByTestId("help-label").click();
    await expect(page.getByTestId("help-dialog")).toBeVisible();
    await expect.poll(fetchedDetails).toBe(true);
  });

  test("the footer links the reference page of the entry, at the anchor of its attribute", async ({
    page,
  }) => {
    const inspector = await selectFirstSpecies(page);
    await attributeRow(inspector, "initialAmount").getByTestId("help-label").click();
    await expect(page.getByTestId("help-dialog")).toBeVisible();

    const link = page.getByTestId("help-docs-link");
    await expect(link).toHaveAttribute("href", /\/reference\/species\/#initialamount$/);
    await expect(link).toHaveAttribute("target", "_blank");
    await expect(link).toHaveAttribute("rel", /noopener/);
  });

  test("a reader who never leaves the keyboard opens the dialog, stays inside it and gets the focus back", async ({
    page,
  }) => {
    const inspector = await selectFirstSpecies(page);
    const label = attributeRow(inspector, "initialAmount").getByTestId("help-label");
    // `.focus()` reaches the label directly instead of tabbing the whole page to it, which would
    // make the test as long as the page is and prove nothing this one does not
    await label.focus();
    await page.keyboard.press("Enter");

    const dialog = page.getByTestId("help-dialog");
    await expect(dialog).toBeVisible();
    await expect.poll(() => query(page, "help")).toBe("types/Species/initialAmount");

    // the dialog is a native modal, so the browser itself keeps the focus inside it; this proves
    // it does for as long as this entry's own focusable elements (the breadcrumb, the type badge,
    // the close button and the documentation link) and a couple more, so a regression which grew
    // or shrank that set would still be caught
    const focusable = dialog.locator("a[href], button:not([disabled])");
    const steps = (await focusable.count()) + 2;
    for (let i = 0; i < steps; i++) {
      await page.keyboard.press("Tab");
    }
    // a string body, not a typed function, the way `referrer.spec.ts` reads `document.referrer`:
    // the e2e project's tsconfig carries no DOM lib, since nothing else here runs in the browser
    const insideDialog = await page.evaluate(
      `document.activeElement?.closest('[data-testid="help-dialog"]') !== null`,
    );
    expect(insideDialog).toBe(true);

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect.poll(() => query(page, "help")).toBeNull();
    await expect(label).toBeFocused();
  });
});
