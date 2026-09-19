import { expect, test, type Locator } from "@playwright/test";

import { openExample } from "./helpers";

/** The cells of the nested tables of the inspector whose content covers more than one line. */
function wrappedCells(column: Locator): Promise<string[]> {
  return column.evaluate((element) => {
    const view = element.ownerDocument.defaultView;
    // the empty cell which closes a table of aligned columns holds nothing to wrap
    return [...element.querySelectorAll('[data-testid="nested-table"] tbody td:not([aria-hidden])')]
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

/** The entries of the type bar which do not fit on their line and are therefore clipped. */
function clippedEntries(bar: Locator): Promise<string[]> {
  return bar.evaluate((element) =>
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

test("the type bar wraps its entries instead of cutting them off or scrolling", async ({
  page,
}) => {
  // a model of eight types, whose entries do not fit on one line of the viewport of the tests
  await openExample(page, "Hepatic_glucose_3 (Hepatic_glucose_3.xml)", 60_000);
  const bar = page.getByTestId("type-bar");
  // `Function definitions` is the longest type name, and the count of a type is at its widest
  // while a search is active, which puts the matches in front of the total
  await expect(bar).toContainText("Function definitions");
  expect(await clippedEntries(bar)).toEqual([]);
  // the row wraps onto as many lines as the model needs, it never scrolls sideways
  expect(
    await bar.evaluate((element) => element.scrollWidth - element.clientWidth),
  ).toBeLessThanOrEqual(0);

  // a search which matches nothing keeps every entry, each with the matches in front of its total
  await page.getByTestId("search-input").fill("zzzz-nothing");
  await expect(page.getByTestId("bar-count-Compartment")).toHaveText("0 / 5");
  await expect(page.getByTestId("bar-count-Parameter")).toHaveText("0 / 258");
  expect(await clippedEntries(bar)).toEqual([]);
  expect(
    await bar.evaluate((element) => element.scrollWidth - element.clientWidth),
  ).toBeLessThanOrEqual(0);
});

test("the type bar lists the types the model uses and the tables are left of the inspector", async ({
  page,
}) => {
  await openExample(page, "BIOMD0000000012");
  const bar = page.getByTestId("type-bar");
  // the repressilator states no function definition and no event, so neither is an entry
  await expect(bar.getByTestId("bar-type-Species")).toBeVisible();
  await expect(bar.getByTestId("bar-type-FunctionDefinition")).toHaveCount(0);
  await expect(bar.getByTestId("bar-type-Event")).toHaveCount(0);

  // the inspector opens at the right of the tables, at about a third of the window
  await page.getByTestId("table-Species").locator("tbody tr[data-pk]").first().click();
  const tables = (await page.getByTestId("tables").boundingBox())!;
  const inspector = (await page.getByTestId("inspector").boundingBox())!;
  expect(inspector.x).toBeGreaterThanOrEqual(tables.x + tables.width);
  const window = page.viewportSize()!;
  expect(inspector.width).toBeGreaterThan(window.width / 4);
  expect(inspector.width).toBeLessThan(window.width / 2);

  // the footer sits under both of them and stays where it is while the tables scroll
  const footer = (await page.getByTestId("app-footer").boundingBox())!;
  expect(footer.y).toBeGreaterThanOrEqual(tables.y + tables.height);
  expect(footer.y).toBeGreaterThanOrEqual(inspector.y + inspector.height);
  await page.getByTestId("tables").evaluate((element) => (element.scrollTop = 400));
  expect((await page.getByTestId("app-footer").boundingBox())!.y).toBe(footer.y);
});

test("the header of the inspector keeps a long type on one line at a laptop width", async ({
  page,
}) => {
  // "User defined constraint component" wrapped onto three lines of the 40 px header at 1280 px
  // and lost its first and last line; the name of the element gives way instead, and in the
  // third of a 1280 px window the end of the type after it, never the id
  const layout = async (width: number) => {
    await page.setViewportSize({ width, height: 800 });
    await page.goto(
      "/examples/fbc_constraints_v3%20(fbc_constraints_v3.xml)?pk=fbc_constraints_v3/UserDefinedConstraintComponent:ratio_v1",
    );
    const header = page.getByTestId("inspector-header");
    await expect(header.getByTestId("inspector-type")).toHaveText(
      "User defined constraint component",
    );
    return header.evaluate((element) => {
      const box = (id: string) => {
        const target = element.querySelector(`[data-testid="${id}"]`)!;
        return {
          height: target.getBoundingClientRect().height,
          clipped: target.scrollWidth > target.clientWidth,
        };
      };
      return {
        header: element.getBoundingClientRect().height,
        type: box("inspector-type"),
        id: box("inspector-id"),
        overflows: element.scrollWidth > element.clientWidth,
      };
    });
  };
  for (const width of [1280, 1440]) {
    const boxes = await layout(width);
    expect(boxes.header).toBe(40);
    expect(boxes.type.height).toBeLessThanOrEqual(20);
    expect(boxes.id.clipped).toBe(false);
    expect(boxes.overflows).toBe(false);
    // from 1440 px on the type is whole
    if (width >= 1440) expect(boxes.type.clipped).toBe(false);
  }
});

test("the sections of the inspector are as high as what they hold in a tall window", async ({
  page,
}) => {
  // in a window taller than the inspector the three sections stretched to a third each, with
  // gaps as high as the sections below their content
  await page.setViewportSize({ width: 1440, height: 1800 });
  await page.goto(
    "/examples/constraint_event%20(constraint_event.xml)?pk=constraint_event/Species:S2",
  );
  const body = page.getByTestId("inspector-body");
  await expect(body.getByTestId("attributes-column")).toBeVisible();
  const gaps = await body.evaluate((element) =>
    [...element.firstElementChild!.children].map((section) => {
      const content = [...section.children].reduce(
        (height, child) => height + child.getBoundingClientRect().height,
        0,
      );
      // the padding of a section is 0.75rem above and below
      return Math.round(section.getBoundingClientRect().height - content - 24);
    }),
  );
  for (const gap of gaps) expect(gap).toBeLessThanOrEqual(8);
});

test("the attributes of the inspector carry their heading in the three columns as well", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1600, height: 900 });
  await page.addInitScript(() => localStorage.setItem("sbml4humans.split.inspector-width", "1100"));
  await page.goto(
    "/examples/constraint_event%20(constraint_event.xml)?pk=constraint_event/Species:S2",
  );
  const heading = page.getByTestId("inspector-body").getByRole("heading", { name: "Attributes" });
  await expect(heading).toBeVisible();
  const references = page.getByTestId("links-references").getByRole("heading");
  // the headings of the three columns stand on one line
  expect((await heading.boundingBox())!.y).toBe((await references.boundingBox())!.y);
});
