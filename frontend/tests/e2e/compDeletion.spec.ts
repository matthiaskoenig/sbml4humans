import { expect, type Page } from "@playwright/test";
import { test } from "@playwright/test";

import { openExample } from "./helpers";

// `comp_deletion.xml` is the example of the composition machinery of comp: the deletions of a
// submodel, the replacements of an element with their conversion factor and their deletion, a
// reference which reaches through a submodel of a submodel and an external model definition.
const EXAMPLE = "comp_deletion (comp_deletion.xml)";

/** The row of an element table, clicked on the cell of its id: every other cell of a comp table
 * holds links of its own, which would navigate instead of selecting the row. */
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

test.describe("comp_deletion", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, EXAMPLE);
  });

  test("links every deletion of a submodel and the element it removes", async ({ page }) => {
    await row(page, "Submodel:cell1").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Submodel");
    const deletions = attribute(page, "listOfDeletions").getByTestId("nested-table");
    await expect(deletions.locator("thead th")).toHaveText(["deletion", "element"]);
    await expect(deletions.locator("tbody tr").first().locator("td")).toHaveText(["del_k", "k"]);

    // the deletion is an element of its own, with the attributes of the file
    await deletions.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Deletion");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("del_k");
    await expect(attribute(page, "idRef")).toContainText("k");
    await expect(inspector.getByTestId("notes")).toContainText("rate constant of the medium");
    // it links the parameter of the submodel which the composed model does not contain
    await inspector
      .getByTestId("links-references")
      .getByTestId("links-deletion")
      .getByTestId("element-link")
      .click();
    await expect(page).toHaveURL(/pk=cell\/Parameter:k$/);
  });

  test("walks from a species over its replacement to the species it replaces", async ({ page }) => {
    await row(page, "Species:glc").click();
    const inspector = page.getByTestId("inspector");
    const replaced = attribute(page, "comp:listOfReplacedElements").getByTestId("nested-table");
    await expect(replaced.locator("tbody tr").first().locator("td")).toHaveText(["cell1", "glc"]);

    await inspector
      .getByTestId("links-references")
      .getByTestId("links-replacedElement")
      .getByTestId("element-link")
      .first()
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ReplacedElement");
    await expect(attribute(page, "submodelRef")).toContainText("cell1");
    await expect(attribute(page, "portRef")).toContainText("glc_port");
    await expect(attribute(page, "conversionFactor")).toContainText("f_amount");

    // the replacement names the submodel and the species inside it which it replaces
    await inspector
      .getByTestId("links-references")
      .getByTestId("links-replacedElement")
      .getByTestId("element-link")
      .nth(1)
      .click();
    await expect(page).toHaveURL(/pk=cell\/Species:glc$/);
    await expect(inspector.getByTestId("inspector-name")).toHaveText("glucose of the cell");
  });

  test("follows a reference through a submodel of a submodel", async ({ page }) => {
    await row(page, "Compartment:medium").click();
    const inspector = page.getByTestId("inspector");
    await inspector
      .getByTestId("links-references")
      .getByTestId("links-replacedElement")
      .getByTestId("element-link")
      .nth(2)
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ReplacedElement");
    await expect(attribute(page, "idRef")).toContainText("cell_in_tissue");
    await expect(attribute(page, "sBaseRef")).toContainText("cell_port");
    // the chain ends at the compartment of the cell inside the tissue
    await inspector
      .getByTestId("links-references")
      .getByTestId("links-replacedElement")
      .getByTestId("element-link")
      .nth(1)
      .click();
    await expect(page).toHaveURL(/pk=cell\/Compartment:c$/);
  });

  test("follows a deletion into the document of an external model definition", async ({ page }) => {
    await row(page, "Submodel:unit_library").click();
    const inspector = page.getByTestId("inspector");
    const deletions = attribute(page, "listOfDeletions").getByTestId("nested-table");
    const cells = deletions.locator("tbody tr").first().locator("td");
    // the example is read from its directory, where the document of the external model
    // definition lies next to it: the unit definition it removes is a link into that document
    await expect(cells.nth(0)).toHaveText("del_external_unit");
    const removed = cells.nth(1).getByTestId("element-link");
    await expect(removed).toHaveAttribute("data-entry", "./unit_definitions.xml");
    await expect(removed.getByTestId("element-link-entry")).toHaveText("unit_definitions.xml");

    // the external model definition carries the checksum of the document it names, and the
    // document which was read has that checksum
    await inspector
      .getByTestId("links-references")
      .getByTestId("links-modelRef")
      .getByTestId("element-link")
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ExternalModelDefinition");
    await expect(attribute(page, "md5")).toContainText("bde1522151d26d8fbca09893ce85ac52");
    await expect(inspector.getByTestId("resolution-status")).toHaveText("resolved");
    await expect(inspector.getByTestId("resolution-md5")).toHaveText("matches the document");
  });
});
