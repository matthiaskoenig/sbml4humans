import { expect, test, type Locator } from "@playwright/test";

import { openExample } from "./helpers";

/** The cells of the nested tables of the inspector whose content covers more than one line. */
function wrappedCells(column: Locator): Promise<string[]> {
  return column.evaluate((element) => {
    const view = element.ownerDocument.defaultView;
    return [...element.querySelectorAll('[data-testid="nested-table"] tbody td')]
      .filter((cell) => {
        // the box of a cell is stretched to the height of its row, so the element inside it is
        // what says how many lines the content of this cell covers
        const content = cell.firstElementChild ?? cell;
        const line = parseFloat(view.getComputedStyle(cell).lineHeight);
        return content.getBoundingClientRect().height > 1.5 * line;
      })
      .map((cell) => cell.textContent.trim());
  });
}

/** The labels of the inspector which do not fit their column and are therefore truncated. */
function truncatedLabels(column: Locator): Promise<string[]> {
  return column.evaluate((element) =>
    [...element.querySelectorAll('[data-testid="attribute-row"] dt')]
      .filter((label) => label.scrollWidth > label.clientWidth)
      .map((label) => label.textContent.trim()),
  );
}

/** The type names of the rail which do not fit next to their count and are therefore clipped. */
function clippedTypes(rail: Locator): Promise<string[]> {
  return rail.evaluate((element) =>
    [...element.querySelectorAll("button")]
      .filter((button) => button.scrollWidth > button.clientWidth)
      .map((button) => button.textContent.trim()),
  );
}

test("the landing page shows the logo in the app bar and in the heading", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("home-page")).toBeVisible();
  const logos = page.getByTestId("app-logo");
  await expect(logos).toHaveCount(2);
  // both images are loaded, not broken, and the bar keeps the height of `h-12`
  for (const logo of await logos.all()) {
    await expect(logo).toBeVisible();
    await expect(logo).toHaveJSProperty("naturalWidth", 192);
  }
  await expect(page.getByTestId("app-bar")).toHaveJSProperty("offsetHeight", 48);
});

test("the nested tables of a reaction keep an identifier on one line", async ({ page }) => {
  await openExample(page, "e_coli_core (e_coli_core.xml.gz)");
  await page.getByTestId("search-input").fill("R_PFK");
  await page.getByTestId("table-Reaction").locator("tbody tr[data-pk]").first().click();
  await expect(page.getByTestId("inspector-id")).toHaveText("R_PFK");

  const column = page.getByTestId("attributes-column");
  // the reactants and the products of the reaction, with the ids of a genome scale model
  await expect(column.getByTestId("nested-table")).toHaveCount(2);
  await expect(column.getByTestId("nested-table").first()).toContainText("M_atp_c");
  expect(await wrappedCells(column)).toEqual([]);
});

test("the reactants of the repressilator keep an identifier on one line", async ({ page }) => {
  await openExample(page, "BIOMD0000000012");
  await page.getByTestId("search-input").fill("Reaction1");
  await page.getByTestId("table-Reaction").locator("tbody tr[data-pk]").first().click();
  await expect(page.getByTestId("inspector-id")).toHaveText("Reaction1");
  expect(await wrappedCells(page.getByTestId("attributes-column"))).toEqual([]);
});

// none of the examples states a local parameter, so the model which exercises their table is
// pasted: two parameters of a kinetic law with the identifiers of a hand written model
const LOCAL_PARAMETERS_MODEL = `<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model id="local_parameters">
    <listOfCompartments>
      <compartment id="cytosol" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="glucose_cytosol" compartment="cytosol" initialConcentration="1"
        hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
      <species id="glucose_6_phosphate_c" compartment="cytosol" initialConcentration="0"
        hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfReactions>
      <reaction id="hexokinase" reversible="false">
        <listOfReactants>
          <speciesReference species="glucose_cytosol" stoichiometry="1" constant="true"/>
        </listOfReactants>
        <listOfProducts>
          <speciesReference species="glucose_6_phosphate_c" stoichiometry="1" constant="true"/>
        </listOfProducts>
        <kineticLaw>
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <apply><times/><ci>Vmax_hexokinase</ci><ci>glucose_cytosol</ci></apply>
          </math>
          <listOfLocalParameters>
            <localParameter id="Vmax_hexokinase" value="2.5"/>
            <localParameter id="Km_glucose_cytosol" value="0.15"/>
          </listOfLocalParameters>
        </kineticLaw>
      </reaction>
    </listOfReactions>
  </model>
</sbml>`;

test("the local parameters of a kinetic law keep an identifier on one line", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(LOCAL_PARAMETERS_MODEL);
  await page.getByTestId("paste-submit").click();
  await expect(page.getByTestId("report-page")).toBeVisible();

  // the kinetic law of the reaction, whose local parameters are a nested table of their own
  await page.getByTestId("table-Reaction").locator("tbody tr[data-pk]").first().click();
  await page
    .getByTestId("attribute-row")
    .filter({ hasText: "kinetic law" })
    .getByTestId("element-link")
    .first()
    .click();
  await expect(page.getByTestId("inspector-type")).toHaveText("Kinetic law");
  const column = page.getByTestId("attributes-column");
  await expect(column.getByTestId("nested-table")).toContainText("Km_glucose_cytosol");
  expect(await wrappedCells(column)).toEqual([]);
});

test("every label of the inspector fits its column", async ({ page }) => {
  await openExample(page, "e_coli_core (e_coli_core.xml.gz)");
  await page.getByTestId("search-input").fill("R_BIOMASS_Ecoli_core_w_GAM");
  await page.getByTestId("table-Reaction").locator("tbody tr[data-pk]").first().click();
  const column = page.getByTestId("attributes-column");
  // `gene product association` is the longest label of any type
  await expect(
    column.getByTestId("attribute-row").filter({ hasText: "gene product association" }),
  ).toBeVisible();
  expect(await truncatedLabels(column)).toEqual([]);
});

test("every type of the rail fits next to its count, with and without a search", async ({
  page,
}) => {
  await openExample(page, "BIOMD0000000012");
  const rail = page.getByTestId("type-rail");
  // `Function definitions` is the longest type name, and the count of a type without elements
  // is the widest one while a search is active
  await expect(rail).toContainText("Function definitions");
  expect(await clippedTypes(rail)).toEqual([]);

  await page.getByTestId("search-input").fill("laci");
  await expect(page.getByTestId("rail-count-FunctionDefinition")).toHaveText("0 / 0");
  expect(await clippedTypes(rail)).toEqual([]);
});
