// Screenshots of the application for the documentation, taken in place of the
// `<!-- screenshot: ... -->` markers of docs/index.md, docs/inputs.md and docs/report.md.
// Usage: start the backend (cd backend && uv run uvicorn sbml4humans.api:api --port 1444) and
// the dev server (cd frontend && npx vite --port 3456), then `npm run screenshots`. Rerun it
// after a change of the user interface, the images are committed alongside the documentation.
import { chromium, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const BASE_URL = "http://localhost:3456";
const API_URL = "http://localhost:1444/api";
const OUT_DIR = fileURLToPath(new URL("../../docs/images/", import.meta.url));

/** Fails with a message that says what to start, instead of a bare connection error, when the
 * dev server or the backend is not up. */
async function checkServer(url, expected) {
  let response;
  try {
    response = await fetch(url);
  } catch {
    response = null;
  }
  if (!response || !response.ok) {
    throw new Error(`${expected} is not reachable at ${url}. Start it before running this script.`);
  }
}

await checkServer(BASE_URL, "the dev server (cd frontend && npx vite --port 3456)");
await checkServer(
  `${API_URL}/examples`,
  "the backend (cd backend && uv run uvicorn sbml4humans.api:api --port 1444)",
);

await mkdir(OUT_DIR, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1600, height: 1000 },
  deviceScaleFactor: 2,
});
// A taller inspector than the default 320px, remembered like a real resize, so the three
// columns of a selected element show their content without the inner scroll clipping it.
await page.addInitScript(() => localStorage.setItem("sbml4humans.split.inspector", "480"));

/** Screenshots `target` (the page by default) as a png of `name` in OUT_DIR. */
function shot(name, target = page, options = {}) {
  return target.screenshot({ path: `${OUT_DIR}${name}.png`, animations: "disabled", ...options });
}

/** Screenshots `locator` cropped to its actual content instead of its full box: a column of the
 * inspector is a stretched grid cell that fills the (enlarged, see below) height of the panel,
 * so its own box reaches well past its content when the content is short. Only leaf elements
 * are measured, since a container such as that grid cell is exactly the box that lies about the
 * content it holds. */
async function shotFitted(name, locator) {
  const box = await locator.boundingBox();
  const contentBottom = await locator.evaluate((element) => {
    let bottom = element.getBoundingClientRect().top;
    for (const node of element.querySelectorAll("*")) {
      if (node.children.length === 0)
        bottom = Math.max(bottom, node.getBoundingClientRect().bottom);
    }
    return bottom;
  });
  const height = Math.min(Math.ceil(contentBottom - box.y) + 16, box.height);
  await page.screenshot({
    path: `${OUT_DIR}${name}.png`,
    animations: "disabled",
    clip: { x: box.x, y: box.y, width: box.width, height },
  });
}

/** Opens the report of an example and waits for the tables. */
async function open(id) {
  await page.goto(`${BASE_URL}/examples/${encodeURIComponent(id)}`);
  await expect(page.getByTestId("report-page")).toBeVisible();
}

/** Selects the row of `table` whose id column is exactly `id` and waits for the inspector to
 * show it. */
async function selectRow(table, id) {
  const row = table
    .locator("tbody tr[data-pk]")
    .filter({ has: page.locator("td:first-child", { hasText: new RegExp(`^${id}$`) }) });
  await row.click();
  await expect(page.getByTestId("inspector-id")).toHaveText(id);
}

// home-inputs.png: the home page with the upload, url and paste tabs
await page.goto(BASE_URL);
await expect(page.getByTestId("home-page")).toBeVisible();
await expect(page.getByTestId("file-dropzone")).toBeVisible();
await shot("home-inputs");

// examples.png: the examples page. The grid holds all the examples (95 at the time of writing)
// stacked in three columns, far taller than the viewport, so this is a viewport shot, not a
// full page one.
await page.goto(`${BASE_URL}/examples`);
await expect.poll(() => page.getByTestId("example-card").count()).toBeGreaterThan(50);
await shot("examples");

// report-tables.png: the repressilator report with nothing selected, so only the type rail and
// the element tables show, no inspector.
await open("BIOMD0000000012");
await expect(page.getByTestId("inspector")).toHaveCount(0);
await shot("report-tables");

// report-overview.png: the same report with an element selected, so the rail, the tables and the
// inspector all show at once.
const speciesTable = page.getByTestId("table-Species");
await selectRow(speciesTable, "PX");
await expect(page.getByTestId("attributes-column")).toBeVisible();
await shot("report-overview");

// inspector-species.png: the inspector of that species alone, with its three columns filled.
await shotFitted("inspector-species", page.getByTestId("inspector"));

// report-search.png: the search box filters every table, the rail counts the matches.
await page.getByTestId("search-input").fill("laci");
await expect(page.getByTestId("rail-count-Species")).toContainText("/");
await shot("report-search");
await page.getByTestId("search-input").press("Escape");

// inspector-annotations.png: an element with resolved annotation labels. icg_body carries an
// indocyanine green species whose SBO term and NCIt resources resolve to a name (the InChIKey
// resource has no label to resolve to, and stays a plain link).
await open("icg_body (icg_body.xml)");
await page.getByTestId("search-input").fill("Cre_plasma_icg");
const icgSpeciesTable = page.getByTestId("table-Species");
await selectRow(icgSpeciesTable, "Cre_plasma_icg");
const annotationsColumn = page.getByTestId("annotations-column");
await expect(annotationsColumn.locator('a[href="https://identifiers.org/CHEBI:31696"]')).toHaveText(
  "indocyanine green",
);
// the annotations of the column alone: its notes and history follow below the visible area of
// the panel, where they would be cut off in the middle of a line
await shotFitted("inspector-annotations", annotationsColumn.locator("section").first());

// archive-entries.png: the top bar of a COMBINE archive report offers its entries for selection.
await open("CompModels");
await expect(page.getByTestId("entry-select")).toBeVisible();
await shot("archive-entries", page.getByTestId("app-bar"));

await browser.close();
