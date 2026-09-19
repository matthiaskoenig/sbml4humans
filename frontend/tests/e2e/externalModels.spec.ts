import { expect, type Page } from "@playwright/test";
import { test } from "@playwright/test";

import { REPOSITORY, openExample, query } from "./helpers";

// `CompModels` is an archive of a comp model, `omex_comp.xml`, whose five submodels instantiate
// the model of another entry, `omex_minimal.xml`, through external model definitions: the
// replaced elements of the one end at the species and the compartment of the other.
const COMP = "./models/omex_comp.xml";
const MINIMAL = "./models/omex_minimal.xml";
const COMP_FILE = `${REPOSITORY}backend/sbml4humans/resources/examples/minimal_model_comp.xml`;

function row(page: Page, pk: string) {
  return page.locator(`tbody tr[data-pk$="${pk}"] td`).first();
}

test.describe("external model definitions", () => {
  test("follows a replaced element into the other entry of the archive and back", async ({
    page,
  }) => {
    await openExample(page, "CompModels", 60_000);
    const entries = page.getByRole("combobox", { name: "archive entry", exact: true });
    await entries.selectOption(COMP);
    await row(page, "Species:S0").click();

    const inspector = page.getByTestId("inspector");
    const replaced = inspector
      .getByTestId("attribute-row")
      .filter({ has: page.locator("dt", { hasText: /^comp:listOfReplacedElements$/ }) })
      .getByTestId("nested-table");
    const target = replaced.locator("tbody tr").first().getByTestId("element-link").last();
    await expect(target).toHaveAttribute("data-entry", MINIMAL);
    await expect(target).toContainText("S1");
    await expect(target.getByTestId("element-link-entry")).toHaveText("omex_minimal.xml");

    // the link opens the report of the other entry on the species the port stands for
    await target.click();
    await expect.poll(() => query(page, "entry")).toBe(MINIMAL);
    expect(query(page, "model")).toBe("omex_minimal");
    expect(query(page, "pk")).toBe("omex_minimal/Species:S1");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Species");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("S1");
    await expect(entries).toHaveValue(MINIMAL);

    // the species lists the five replacements which name it from the other entry
    const back = inspector
      .getByTestId("links-referenced-by")
      .getByTestId("links-replacedElement")
      .getByTestId("element-link");
    await expect(back).toHaveCount(5);
    await expect(back.first()).toHaveAttribute("data-entry", COMP);
    await back.first().click();
    await expect.poll(() => query(page, "entry")).toBe(COMP);
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ReplacedElement");

    // the browser goes back over the entries
    await page.goBack();
    await expect.poll(() => query(page, "entry")).toBe(MINIMAL);
    await expect(inspector.getByTestId("inspector-id")).toHaveText("S1");
  });

  test("names the model and the document at the external model definition", async ({ page }) => {
    await openExample(page, "CompModels", 60_000);
    await page.goto(
      `/examples/CompModels?entry=${encodeURIComponent(COMP)}&pk=${encodeURIComponent("document/ExternalModelDefinition:emd0")}`,
    );
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("resolution-status")).toHaveText("resolved");
    await expect(inspector.getByTestId("resolution-entry")).toHaveText(MINIMAL);
    await inspector.getByTestId("resolution-model").click();
    await expect.poll(() => query(page, "entry")).toBe(MINIMAL);
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Model");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("omex_minimal");
  });

  test("says that an upload of the file alone has no document to follow", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("file-input").setInputFiles(COMP_FILE);
    await expect(page.getByTestId("report-page")).toBeVisible({ timeout: 30_000 });
    await row(page, "Submodel:submodel0").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("resolution-status")).toHaveText(
      "no document at the source",
    );
    // nothing is read next to an upload, the archive has the one entry
    await expect(page.getByTestId("entry-select")).toHaveCount(0);
  });
});
