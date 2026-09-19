import { expect, type Page } from "@playwright/test";
import { test } from "@playwright/test";

import { openExample } from "./helpers";

// The uncertainty of a value: the interval a span stands for, the parameters a distribution is
// defined by and the elements a measure names instead of writing a number.
const SPANS = "distrib_spans (distrib_spans.xml)";
const UNCERTAINTIES = "distrib_uncertainties (distrib_uncertainties.xml)";

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

/** The measures of the uncertainty the inspector shows, as "<name> <type> <value>" per row,
 * where a measure without an identifier of its own is named by its type alone. */
async function measures(page: Page): Promise<string[]> {
  const rows = attribute(page, "uncert parameters").getByTestId("nested-table").locator("tbody tr");
  return rows.evaluateAll((elements) =>
    elements.map((element) =>
      [
        element.querySelector("[data-testid=uncert-measure] [data-testid=element-link]"),
        element.querySelector("[data-testid=uncert-type]"),
        element.querySelector("[data-testid=uncert-value]"),
      ]
        .map((part) => part?.textContent?.replace(/\s+/g, " ").trim())
        .filter((text) => !!text)
        .join(" "),
    ),
  );
}

test.describe("distrib", () => {
  test("shows the range of the shipped example as the interval it is", async ({ page }) => {
    await openExample(page, UNCERTAINTIES);
    await row(page, "Parameter:p1").click();
    await attribute(page, "uncertainties").getByTestId("element-link").first().click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Uncertainty");
    // the report read the span as a plain parameter and showed the word "range" with five
    // empty cells behind it
    expect(await measures(page)).toEqual([
      "range 1 to 4",
      "mean 2",
      "standardDeviation 2",
      "distribution normal(2,2)",
    ]);
  });

  test("links the two ends of a span to the parameters which hold them", async ({ page }) => {
    await openExample(page, SPANS);
    await row(page, "Parameter:Km").click();
    const inspector = page.getByTestId("inspector");
    // a measurement per publication is an uncertainty of its own, and the inspector of the
    // parameter shows the measures of each of them
    const uncertainties = attribute(page, "uncertainties").getByTestId("uncertainty");
    await expect(uncertainties.getByTestId("uncertainty-name")).toHaveText([
      /^u_Km_purified\s*Wilson 1997, purified enzyme$/,
      /^u_Km_lysate\s*Baker 2012, cell lysate$/,
    ]);
    await expect(uncertainties.nth(0).getByTestId("uncert-value")).toHaveText([
      "0.5",
      "0.06",
      "12",
      "0.38 to 0.63",
    ]);
    await uncertainties.nth(1).getByTestId("uncertainty-name").getByTestId("element-link").click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Uncertainty");
    expect(await measures(page)).toEqual([
      "median 0.59",
      "Km_lysate_ci confidenceInterval Km_lower to Km_upper",
    ]);

    // the ends of the interval are elements of the model and the report walks to them, and the
    // element says which end of which interval it holds
    await inspector.getByTestId("uncert-span").getByTestId("element-link").first().click();
    await expect(page).toHaveURL(/pk=distrib_spans\/Parameter:Km_lower$/);
    await expect(
      inspector.getByTestId("links-referenced-by").getByTestId("links-varLower"),
    ).toContainText("Km_lysate_ci");

    // the uncertainty leads back to the element whose value it describes, and the search finds
    // the element by what its uncertainties say
    await page.goBack();
    await inspector
      .getByTestId("links-referenced-by")
      .getByTestId("links-uncertainty")
      .getByTestId("element-link")
      .click();
    await expect(page).toHaveURL(/pk=distrib_spans\/Parameter:Km$/);
    await page.getByTestId("search-input").fill("Baker");
    await expect(page.getByTestId("table-Parameter").locator("tbody tr[data-pk]")).toHaveCount(1);
  });

  test("shows the parameters a distribution is defined by", async ({ page }) => {
    await openExample(page, SPANS);
    await row(page, "Parameter:Vmax").click();
    const inspector = page.getByTestId("inspector");
    await attribute(page, "uncertainties").getByTestId("element-link").first().click();
    expect(await measures(page)).toEqual([
      "Vmax_mean_measure mean Vmax_mean",
      "Vmax_distribution distribution -",
      "Vmax_alpha externalParameter 2",
      "Vmax_beta externalParameter 5",
    ]);
    // the two parameters of the Beta distribution sit one level below it
    const depths = await attribute(page, "uncert parameters")
      .getByTestId("uncert-measure")
      .evaluateAll((elements) => elements.map((element) => element.getAttribute("data-depth")));
    expect(depths).toEqual(["0", "0", "1", "1"]);

    // a parameter is an element of its own, with the definition which says what it means
    await attribute(page, "uncert parameters")
      .getByTestId("uncert-measure")
      .getByTestId("element-link")
      .nth(2)
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Uncert parameter");
    await expect(attribute(page, "type")).toContainText("externalParameter");
    await expect(attribute(page, "value")).toContainText("2");
    await expect(attribute(page, "definition").getByTestId("definition-link")).toHaveText("alpha");
  });

  test("walks a measure to the element and the units it names", async ({ page }) => {
    await openExample(page, SPANS);
    await row(page, "Parameter:Vmax").click();
    const inspector = page.getByTestId("inspector");
    await attribute(page, "uncertainties").getByTestId("element-link").first().click();
    await attribute(page, "uncert parameters")
      .getByTestId("uncert-measure")
      .getByTestId("element-link")
      .first()
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Uncert parameter");
    // the mean is not a number but the parameter which holds it, and it carries its own units
    await expect(attribute(page, "var").getByTestId("element-link")).toHaveText("Vmax_mean");
    await expect(attribute(page, "units").getByTestId("element-link")).toHaveText(
      "mmole_per_min_l",
    );
    await attribute(page, "units").getByTestId("element-link").click();
    await expect(page).toHaveURL(/pk=distrib_spans\/UnitDefinition:mmole_per_min_l$/);
  });

  test("links the math of a distribution from the parameter which carries it", async ({ page }) => {
    await openExample(page, SPANS);
    await row(page, "AssignmentRule:v").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Assignment rule");
    await attribute(page, "uncertainties").getByTestId("element-link").first().click();
    // the math of the uncertainty belongs to the parameter which writes it, not to the
    // uncertainty around it
    await expect(inspector.getByTestId("links-references").getByTestId("links-math")).toHaveCount(
      0,
    );
    await attribute(page, "uncert parameters")
      .getByTestId("uncert-measure")
      .getByTestId("element-link")
      .nth(1)
      .click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Uncert parameter");
    await expect(inspector.getByTestId("links-references").getByTestId("links-math")).toContainText(
      "Vmax_mean",
    );
  });
});
