import { expect, type Page } from "@playwright/test";
import { test } from "@playwright/test";

import { openExample } from "./helpers";

// A qualitative model: the levels of its species, the influences of its transitions with the
// sign of each of them, and the function terms as the transition table they are.
const QUAL = "qual_example (qual_example.xml)";

/** The row of an element table, clicked on the cell of its id: another cell holds links of its
 * own, which would navigate instead of selecting the row. */
function row(page: Page, pk: string) {
  return page.locator(`tbody tr[data-pk$="${pk}"] td`).first();
}

/** The attribute row of the inspector with that label. */
function attribute(page: Page, label: string) {
  return page
    .getByTestId("inspector")
    .getByTestId("attribute-row")
    .filter({ has: page.locator("dt", { hasText: new RegExp(`^${label}$`) }) });
}

test.describe("qual", () => {
  test("shows the qualitative species of a model with their levels", async ({ page }) => {
    await openExample(page, QUAL);
    await expect(page.getByTestId("table-QualitativeSpecies").locator("thead th")).toHaveText([
      "id",
      "name",
      "compartment",
      "initial level",
      "max level",
      "constant",
    ]);

    await row(page, "QualitativeSpecies:P").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Qualitative species");
    await expect(attribute(page, "initial level")).toContainText("1");
    await expect(attribute(page, "max level")).toContainText("2");
    // the input of the system carries no initial level at all
    await row(page, "QualitativeSpecies:S").click();
    await expect(attribute(page, "initial level")).toContainText("-");
    await expect(attribute(page, "constant")).toBeVisible();
  });

  test("shows the influence of a transition with the sign of every input", async ({ page }) => {
    await openExample(page, QUAL);
    const transition = page.locator('tbody tr[data-pk$="Transition:tr_G"]');
    // the cell of the inputs names the species and the sign of the influence of each of them
    await expect(transition.getByTestId("influence").first()).toContainText("S");
    await expect(transition.getByTestId("influence").first().getByTestId("qual-sign")).toHaveText([
      "+",
      "−",
      "+",
    ]);

    await row(page, "Transition:tr_G").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Transition");
    const inputs = attribute(page, "inputs").getByTestId("nested-table");
    await expect(inputs.locator("thead th")).toHaveText([
      "id",
      "species",
      "sign",
      "threshold",
      "effect",
    ]);
    await expect(inputs.locator("tbody tr").nth(1).locator("td").nth(3)).toHaveText("2");

    // an input is an element of its own and names the species it reads
    await inputs.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Input");
    await expect(attribute(page, "transition effect")).toContainText("none");
    await attribute(page, "qualitative species").getByTestId("element-link").click();
    await expect(page).toHaveURL(/pk=qual_example\/QualitativeSpecies:S$/);
    // the species says which transitions read it, which is the influence graph backwards
    await expect(
      inspector.getByTestId("links-referenced-by").getByTestId("links-input"),
    ).toContainText("theta_G_S");
  });

  test("shows the function terms of a transition as its transition table", async ({ page }) => {
    await openExample(page, QUAL);
    await row(page, "Transition:tr_P").click();
    const inspector = page.getByTestId("inspector");
    const terms = attribute(page, "function terms").getByTestId("nested-table");
    await expect(terms.locator("thead th")).toHaveText(["term", "condition", "result level"]);
    const rows = terms.locator("tbody tr");
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(0).locator("td").nth(2)).toHaveText("2");
    // the default term is the last row and holds wherever no condition does
    await expect(rows.nth(2)).toContainText("otherwise");
    await expect(rows.nth(2).locator("td").nth(2)).toHaveText("0");

    // the output of a Petri net transition produces a level per result level
    const outputs = attribute(page, "outputs").getByTestId("nested-table");
    await expect(outputs.locator("tbody tr").first().locator("td").nth(3)).toHaveText("production");
    await outputs.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Output");
    await expect(attribute(page, "output level")).toContainText("1");
  });

  test("walks the math of a function term to the species and the input it names", async ({
    page,
  }) => {
    await openExample(page, QUAL);
    await row(page, "Transition:tr_G").click();
    const inspector = page.getByTestId("inspector");
    const terms = attribute(page, "function terms").getByTestId("nested-table");
    await terms.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Function term");
    await expect(attribute(page, "result level")).toContainText("1");

    // the symbols of the condition are the species whose level and the input whose threshold
    // it compares, each a link of its own: the text `theta_G_S` contains the `S` of the species
    const links = inspector
      .getByTestId("links-references")
      .getByTestId("links-math")
      .getByTestId("element-link");
    await expect(links).toHaveCount(4);
    expect((await links.allTextContents()).map((text) => text.trim()).sort()).toEqual([
      "P",
      "S",
      "theta_G_P",
      "theta_G_S",
    ]);
  });
});
