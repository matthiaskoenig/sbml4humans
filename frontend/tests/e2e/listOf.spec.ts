import { expect, test } from "@playwright/test";

import { openExample, query } from "./helpers";

// `list_of.xml` is the example of the lists which state something of their own: the model owns
// a `listOfSpecies` with an id, an SBO term, notes and an annotation, a `listOfUnitDefinitions`
// with a name and an empty `listOfRules` with a note, a reaction and a unit definition own a
// list each, and a port names the list of the species by its meta id.
const EXAMPLE = "list_of (list_of.xml)";

test.describe("list_of", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, EXAMPLE);
  });

  test("links the list of a table from its heading and opens it in the inspector", async ({
    page,
  }) => {
    const link = page.getByTestId("section-Species").getByTestId("section-list");
    await expect(link).toHaveText("metabolites");
    // the list of the compartments states nothing, its table has no link
    await expect(page.getByTestId("section-Compartment").getByTestId("section-list")).toHaveCount(
      0,
    );

    await link.getByTestId("element-link").click();
    expect(query(page, "pk")).toBe("list_of/ListOf:metabolites");
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ListOf");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("metabolites");
    await expect(inspector.getByTestId("inspector-name")).toHaveText(
      "the metabolites of the pathway",
    );
    const rows = inspector.getByTestId("attributes-column").getByTestId("attribute-row");
    await expect(rows.filter({ hasText: "list" })).toContainText("listOfSpecies");
    await expect(rows.filter({ hasText: "size" })).toContainText("2");
    await expect(inspector.getByTestId("notes")).toContainText(
      "The species of this list are the two metabolites of the pathway",
    );
    await expect(
      inspector.getByTestId("cvterm").filter({ hasText: "BQB_IS_PART_OF" }),
    ).toContainText("GO:0006096");
    // the list names the model which owns it and the port which names it
    const referencedBy = inspector.getByTestId("links-referenced-by");
    await expect(referencedBy.getByTestId("links-listOf")).toContainText("list_of");
    await expect(referencedBy.getByTestId("links-port")).toContainText("metabolites_port");
  });

  test("shows the xml of a list without its elements", async ({ page }) => {
    await page.getByTestId("section-Species").getByTestId("section-list").locator("a").click();
    const inspector = page.getByTestId("inspector");
    await inspector.getByTestId("inspector-xml-toggle").click();
    const xml = inspector.getByTestId("xml-view");
    await expect(xml).toContainText("<listOfSpecies");
    await expect(xml).toContainText("bqbiol:isPartOf");
    await expect(xml).not.toContainText("<species");
  });

  test("lists the lists of the model, the empty one with its note", async ({ page }) => {
    // the report opens with its model in the inspector
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Model");
    const lists = inspector.getByTestId("lists").getByTestId("element-link");
    await expect(lists).toHaveText(["listOfUnitDefinitions", "metabolites", "listOfRules"]);

    // the model has no rules and so no table of them: the model is where the list is found
    await expect(page.getByTestId("section-AssignmentRule")).toHaveCount(0);
    await lists.filter({ hasText: "listOfRules" }).click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ListOf");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("listOfRules");
    const rows = inspector.getByTestId("attributes-column").getByTestId("attribute-row");
    await expect(rows.filter({ hasText: "size" })).toContainText("0");
    await expect(inspector.getByTestId("notes")).toContainText("the list is empty on purpose");
  });

  test("lists the list of a reaction in the inspector of the reaction", async ({ page }) => {
    await page.getByTestId("table-Reaction").locator('tbody tr[data-pk$="Reaction:J0"]').click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Reaction");
    const lists = inspector.getByTestId("lists").getByTestId("element-link");
    await expect(lists).toHaveText(["J0.listOfReactants"]);
    await lists.first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ListOf");
    await expect(inspector.getByTestId("inspector-name")).toHaveText("what J0 consumes");
  });

  test("links the list a port names by its meta id", async ({ page }) => {
    const row = page
      .getByTestId("table-Port")
      .locator('tbody tr[data-pk$="Port:metabolites_port"]');
    const link = row.getByTestId("element-link").filter({ hasText: "meta_species" });
    await expect(link).toHaveAttribute("data-pk", "list_of/ListOf:metabolites");
    await link.click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("ListOf");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("metabolites");
  });
});
