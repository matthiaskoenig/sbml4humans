import { expect, test } from "@playwright/test";

import { openExample } from "./helpers";

// `constraint_event.xml` is the example of the objects of core which carry attributes of their
// own: the units of a unit definition, the message of a constraint and the trigger, the priority
// and the delay of an event.
const EXAMPLE = "constraint_event (constraint_event.xml)";

test.describe("constraint_event", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, EXAMPLE);
  });

  test("shows the units a unit definition is built from next to its formula", async ({ page }) => {
    await page
      .getByTestId("table-UnitDefinition")
      .locator('tbody tr[data-pk$="UnitDefinition:mmole_per_min_l"]')
      .click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Unit definition");
    const units = inspector.getByTestId("nested-table");
    await expect(units.locator("thead th")).toHaveText(["kind", "exponent", "scale", "multiplier"]);
    await expect(units.locator("tbody tr")).toHaveCount(3);
    await expect(units.locator("tbody tr").first().locator("td")).toHaveText([
      "mole",
      "1",
      "-3",
      "1",
    ]);
  });

  test("renders the message of a constraint as xhtml, in the table and in the inspector", async ({
    page,
  }) => {
    const row = page.getByTestId("table-Constraint").locator("tbody tr[data-pk]").first();
    await expect(row.getByTestId("xhtml").locator("b").first()).toHaveText("S1");
    await row.click();
    const message = page.getByTestId("inspector").getByTestId("message");
    await expect(message.locator("b").first()).toHaveText("S1");
    await expect(message).not.toContainText("<message>");
  });

  test("opens the trigger of an event and walks to the parameter its condition reads", async ({
    page,
  }) => {
    // the cell of the id, because the cell of the assignments holds links of its own
    await page
      .getByTestId("table-Event")
      .locator("tbody tr[data-pk]")
      .first()
      .locator("td")
      .first()
      .click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-id")).toHaveText("E1");

    await inspector.getByTestId("element-link").filter({ hasText: "E1_trigger" }).click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Trigger");
    await expect(inspector.getByTestId("notes")).toContainText("twenty minutes");

    // the math of the trigger is read by the trigger, not by the event around it
    await inspector
      .getByTestId("links-references")
      .getByTestId("links-math")
      .getByTestId("element-link")
      .click();
    await expect(inspector.getByTestId("inspector-id")).toHaveText("t_dose");
  });
});
