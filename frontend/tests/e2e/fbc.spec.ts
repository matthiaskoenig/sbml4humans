import { expect, type Page } from "@playwright/test";
import { test } from "@playwright/test";

import { openExample } from "./helpers";

// The three shapes of fbc the report reads: the flux bounds of a Version 1 document, the user
// defined constraints and the key value pairs of a Version 3 one, and the gene product
// association and the columns of a genome scale model of Version 2.
const V1 = "fbc_bounds_v1 (fbc_bounds_v1.xml)";
const V3 = "fbc_constraints_v3 (fbc_constraints_v3.xml)";
const ECOLI = "e_coli_core (e_coli_core.xml.gz)";

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

/** The headers of the table of an element type. */
function headers(page: Page, type: string) {
  return page.getByTestId(`table-${type}`).locator("thead th");
}

test.describe("fbc", () => {
  test("shows the flux bounds of a Version 1 model with the reaction they constrain", async ({
    page,
  }) => {
    await openExample(page, V1);
    await expect(headers(page, "FluxBound")).toHaveText([
      "id",
      "name",
      "reaction",
      "operation",
      "value",
    ]);
    await row(page, "FluxBound:v1_lb").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Flux bound");
    await expect(attribute(page, "operation")).toContainText("greaterEqual");
    await expect(attribute(page, "value")).toContainText("0");

    // the bound names the reaction it constrains, and the reaction lists both of its bounds
    await attribute(page, "reaction").getByTestId("element-link").click();
    await expect(page).toHaveURL(/pk=fbc_bounds_v1\/Reaction:v1$/);
    await expect(
      inspector.getByTestId("links-referenced-by").getByTestId("links-fluxBound"),
    ).toContainText("v1_ub");
    // a reaction of a Version 1 document has no fbc attributes of its own
    await expect(attribute(page, "lower flux bound")).toHaveCount(0);
  });

  test("shows the active objective and the flux objectives of a model", async ({ page }) => {
    await openExample(page, V1);
    await page.getByTestId("bar-model").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Model");
    await expect(attribute(page, "strict")).toContainText("-");
    await attribute(page, "active objective").getByTestId("element-link").click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Objective");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("biomass_max");

    // the objective lists its terms, and every term is an element with its own reaction
    const terms = attribute(page, "flux objectives").getByTestId("nested-table");
    await expect(terms.locator("tbody tr").first().locator("td").nth(1)).toHaveText("EX_biomass");
    await terms.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Flux objective");
    await expect(attribute(page, "coefficient")).toContainText("1");
  });

  test("walks a user defined constraint of a Version 3 model to its variables", async ({
    page,
  }) => {
    await openExample(page, V3);
    await row(page, "UserDefinedConstraint:ratio").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("User defined constraint");
    await expect(attribute(page, "lower bound")).toContainText("ratio_lb");
    const components = attribute(page, "components").getByTestId("nested-table");
    await expect(components.locator("tbody tr")).toHaveCount(2);
    await expect(components.locator("tbody tr").first().locator("td").nth(1)).toHaveText("v1");

    // the component is an element of its own and links the parameter of its coefficient
    await components.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText(
      "User defined constraint component",
    );
    await attribute(page, "coefficient").getByTestId("element-link").click();
    await expect(page).toHaveURL(/pk=fbc_constraints_v3\/Parameter:c_two$/);
    // the parameter of the coefficient says which constraints weigh a flux with it
    await expect(
      inspector.getByTestId("links-referenced-by").getByTestId("links-coefficient"),
    ).toBeVisible();
  });

  test("shows the key value pairs an element of a Version 3 model carries", async ({ page }) => {
    await openExample(page, V3);
    await row(page, "Parameter:maintenance").click();
    const pairs = attribute(page, "key value pairs").getByTestId("nested-table");
    await expect(pairs.locator("thead th")).toHaveText(["key", "value", "uri"]);
    await expect(pairs.locator("tbody tr").first().locator("td")).toHaveText([
      "source",
      "measured",
      "https://sbml.org/fbc/keyvaluepair",
    ]);
  });

  test("renders the gene product association of a reaction as its tree", async ({ page }) => {
    await openExample(page, V3);
    await row(page, "Reaction:v1").click();
    const inspector = page.getByTestId("inspector");
    const association = attribute(page, "gene product association");
    await expect(association).toContainText("((g_ptsG and g_ptsH) or g_galP)");

    // every gene of the tree is a link to its gene product
    await association.getByTestId("element-link").nth(1).click();
    await expect(page).toHaveURL(/pk=fbc_constraints_v3\/GeneProduct:g_ptsG$/);
    await expect(attribute(page, "label")).toContainText("b1101");

    // the gene names the reference which reads it, and the reference its association
    await inspector
      .getByTestId("links-referenced-by")
      .getByTestId("links-geneProduct")
      .getByTestId("element-link")
      .first()
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Gene product reference");
    await inspector
      .getByTestId("links-referenced-by")
      .getByTestId("links-geneProductAssociation")
      .getByTestId("element-link")
      .first()
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("And");
  });

  test("gives the tables of a genome scale model their fbc columns", async ({ page }) => {
    await openExample(page, ECOLI, 60_000);
    // the chemical formula and the charge of a species, next to its compartment
    await expect(headers(page, "Species")).toContainText(["formula", "charge"]);
    await expect(
      page.getByTestId("table-Species").locator("tbody tr").first().locator("td").nth(3),
    ).toHaveText("C6H12O6");

    // the bounds and the gene association of a reaction, one line per reaction
    await expect(headers(page, "Reaction")).toContainText([
      "lower bound",
      "upper bound",
      "gene association",
    ]);
    const reaction = page.locator('tbody tr[data-pk$="Reaction:R_PFK"]');
    await expect(reaction.getByTestId("gene-cell")).toHaveText("(G_b3916 or G_b1723)");
    // a model without the package keeps the columns it had
    await openExample(page, "BIOMD0000000012 (BIOMD0000000012_urn.xml)");
    await expect(headers(page, "Species")).not.toContainText(["formula"]);
  });
});
