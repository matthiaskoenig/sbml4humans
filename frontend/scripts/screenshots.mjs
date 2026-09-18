// Screenshots of the application for the documentation, taken in place of the
// `<!-- screenshot: ... -->` markers of docs/index.md, docs/inputs.md and docs/report.md.
// Usage: start the backend (cd backend && uv run uvicorn sbml4humans.api:api --port 1444) and
// the dev server (cd frontend && npx vite --port 3456), then `npm run screenshots`. Rerun it
// after a change of the user interface, the images are committed alongside the documentation.
//
// The article column of the built site is COLUMN_WIDTH wide and renders an image at its own
// width up to that, so an image of that width is read at the size the application draws it.
// A page and a part of the report are therefore captured that wide. The report as a whole
// needs its rail, its tables and its inspector next to each other, which no window that narrow
// shows: it is captured in REPORT_VIEWPORT, the narrowest window in which the bar of a report
// states its entry and its model in full, and the documentation links those three images to
// their file, so that a click opens them at full size.
import { chromium, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const BASE_URL = "http://localhost:3456";
const API_URL = "http://localhost:1444/api";
const OUT_DIR = fileURLToPath(new URL("../../docs/images/", import.meta.url));

// the width of the article column of the built site, in CSS pixels
const COLUMN_WIDTH = 757;
// the window a page (the home page, the examples) is captured in: as wide as that column
const PAGE_VIEWPORT = { width: COLUMN_WIDTH, height: 900 };
// the window the report as a whole is captured in: the narrowest one in which the bar states
// the entry and the model of a report in full and no value of the inspector is broken inside a
// token, which a narrower window does to a value such as `SBO:0000252`
const REPORT_VIEWPORT = { width: 1200, height: 760 };
// a window wide enough for one of the three columns of the inspector to be as wide as the
// article column: the inspector spans the report without its rail of 256 px and its divider,
// and every one of its three columns carries 12 px of padding on each side
const WIDE_VIEWPORT = { width: 3 * (COLUMN_WIDTH + 24) + 256 + 4, height: 1000 };
// the height of the inspector, as if the divider had been dragged there. The shots of the
// inspector itself open it far enough for its three columns to show their content instead of
// scrolling inside the panel, the report as a whole opens it at the height of the element it
// shows.
const TALL_INSPECTOR_HEIGHT = 480;

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
try {
  /** A page of the given window size, with the height of the inspector remembered the way a
   * real resize remembers it. */
  async function newPage(viewport, inspectorHeight = TALL_INSPECTOR_HEIGHT) {
    const page = await browser.newPage({ viewport, deviceScaleFactor: 2 });
    await page.addInitScript(
      (height) => localStorage.setItem("sbml4humans.split.inspector", String(height)),
      inspectorHeight,
    );
    return page;
  }

  /** Screenshots `target` (a page or a locator) as a png of `name` in OUT_DIR. */
  function shot(name, target, options = {}) {
    return target.screenshot({ path: `${OUT_DIR}${name}.png`, animations: "disabled", ...options });
  }

  /** Screenshots the part of `page` between the top of `from` and the bottom of `to`, over the
   * whole width of the window: the form of the home page or the first cards of the examples,
   * without the empty space which follows them. */
  async function shotBetween(name, page, from, to) {
    const top = (await from.boundingBox()).y;
    const end = await to.boundingBox();
    await shot(name, page, {
      clip: {
        x: 0,
        y: top - 8,
        width: page.viewportSize().width,
        height: end.y + end.height - top + 16,
      },
    });
  }

  /** The bottom of the content of `locator`, in page coordinates. Only leaf elements are
   * measured, since a container such as a stretched grid cell is exactly the box that lies
   * about the content it holds. */
  function contentBottom(locator) {
    return locator.evaluate((element) => {
      let bottom = element.getBoundingClientRect().top;
      for (const node of element.querySelectorAll("*")) {
        if (node.children.length === 0)
          bottom = Math.max(bottom, node.getBoundingClientRect().bottom);
      }
      return bottom;
    });
  }

  /** Screenshots `locator` cropped to its content instead of to its full box: a column of the
   * inspector is a stretched grid cell that fills the height of the panel, so its own box
   * reaches well past its content when the content is short. */
  async function shotFitted(name, page, locator) {
    const box = await locator.boundingBox();
    const height = Math.min(Math.ceil((await contentBottom(locator)) - box.y) + 16, box.height);
    await shot(name, page, { clip: { x: box.x, y: box.y, width: box.width, height } });
  }

  /** Moves the pointer out of the way and waits for the tooltip it may have opened to go: a
   * pointer left on a link or on a column header by a click would otherwise put a tooltip into
   * the next screenshot, and a different one on every run. */
  async function restPointer(page) {
    await page.mouse.move(2, page.viewportSize().height - 2);
    await expect(page.getByRole("tooltip")).toHaveCount(0);
  }

  /** Opens the report of an example and waits for the tables. */
  async function open(page, id) {
    await page.goto(`${BASE_URL}/examples/${encodeURIComponent(id)}`);
    await expect(page.getByTestId("report-page")).toBeVisible();
  }

  /** Escapes the characters a regular expression gives a meaning to, so that an id such as
   * `icg_body (icg_body.xml)` matches itself and nothing else. */
  function escaped(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  /** Selects the row of `table` whose id column is exactly `id` and waits for the inspector to
   * show it. The click goes to the id cell of the row rather than to the middle of it, where a
   * wide window puts a cell which holds a link, and a click on a link selects what it points at
   * instead of the row. */
  async function selectRow(page, table, id) {
    const row = table
      .locator("tbody tr[data-pk]")
      .filter({ has: page.locator("td:first-child", { hasText: new RegExp(`^${escaped(id)}$`) }) });
    await expect(row).toHaveCount(1);
    await row.locator("td").first().click();
    await expect(page.getByTestId("inspector-id")).toHaveText(id);
  }

  /** The height the open inspector needs for the content of its columns, which is the height
   * the report as a whole is captured with: taller and the panel ends in empty space, shorter
   * and its columns scroll inside it. */
  async function inspectorHeight(page) {
    const panel = page.getByTestId("inspector");
    const top = (await panel.boundingBox()).y;
    return Math.ceil((await contentBottom(panel)) - top) + 8;
  }

  /** The heights at which the tables can be cut without cutting a row in half, measured from
   * the top of the visible part of the pane: the bottom of every row and of every section. A
   * picture which ends in the upper pixels of a row is read as a rendering fault rather than as
   * the edge of the picture.  */
  function cutPoints(page) {
    return page.getByTestId("tables").evaluate((pane) => {
      const top = pane.getBoundingClientRect().top;
      return [...pane.querySelectorAll("tbody tr[data-pk], section")]
        .map((node) => node.getBoundingClientRect().bottom - top)
        .filter((offset) => offset > 0);
    });
  }

  /** The greatest of those heights which stays within `limit`. */
  async function cutWithin(page, limit) {
    return Math.max(...(await cutPoints(page)).filter((offset) => offset <= limit));
  }

  /** Scrolls the tables to the section of `type`, with its heading at the top of the pane. */
  async function scrollToSection(page, type) {
    await page.getByTestId(`section-${type}`).evaluate((section) => {
      section.scrollIntoView({ block: "start" });
      // `scroll-mt-2` leaves the last 8 px above the section in view, which is the lower
      // border of the table before it
      section.parentElement.scrollTop += 8;
    });
  }

  // the pages of the application, in a window as wide as the column of the site
  const pages = await newPage(PAGE_VIEWPORT);

  // home-inputs.png: the home page with the upload, url and paste tabs, cropped to the form
  await pages.goto(BASE_URL);
  await expect(pages.getByTestId("home-page")).toBeVisible();
  await expect(pages.getByTestId("file-dropzone")).toBeVisible();
  await shotBetween(
    "home-inputs",
    pages,
    pages.getByTestId("home-tab-upload"),
    pages.getByTestId("home-examples-link"),
  );

  // examples.png: the filter and the first cards of the examples page. The grid holds all the
  // examples (95 at the time of writing), far taller than any window, so the picture ends below
  // the third row of cards.
  await pages.goto(`${BASE_URL}/examples`);
  await expect.poll(() => pages.getByTestId("example-card").count()).toBeGreaterThan(50);
  await shotBetween(
    "examples",
    pages,
    pages.getByTestId("examples-page"),
    pages.getByTestId("example-card").nth(5),
  );
  await pages.close();

  // the report as a whole: the type rail, the element tables and the inspector
  const report = await newPage(REPORT_VIEWPORT);

  // report-tables.png: the repressilator report with nothing selected, so only the type rail and
  // the element tables show, no inspector.
  await open(report, "BIOMD0000000012");
  await expect(report.getByTestId("inspector")).toHaveCount(0);
  const tables = await report.getByTestId("tables").boundingBox();
  await restPointer(report);
  await shot("report-tables", report, {
    clip: {
      x: 0,
      y: 0,
      width: REPORT_VIEWPORT.width,
      height: tables.y + (await cutWithin(report, tables.height)),
    },
  });

  // inspector-species.png: the inspector of a species alone, with its three columns filled.
  await selectRow(report, report.getByTestId("table-Species"), "PX");
  await expect(report.getByTestId("attributes-column")).toBeVisible();
  // the label of the SBO term of the species is resolved in a request of its own, and the
  // height of the column depends on it: without this the picture and the height of the panel
  // below differ from run to run
  await expect(
    report
      .getByTestId("annotations-column")
      .locator('a[href="https://identifiers.org/SBO:0000252"]'),
  ).toHaveText("polypeptide chain");
  await restPointer(report);
  await shotFitted("inspector-species", report, report.getByTestId("inspector"));

  // the height the inspector of that species needs, and the height of the tables next to it:
  // the report as a whole opens the inspector so that its columns show their content and the
  // tables end between two rows
  const needed = await inspectorHeight(report);
  await scrollToSection(report, "Species");
  const withTables = await report.getByTestId("tables").boundingBox();
  const cut = await cutWithin(report, withTables.height + TALL_INSPECTOR_HEIGHT - needed);
  const inspector = TALL_INSPECTOR_HEIGHT + withTables.height - cut;

  // report-search.png: the search box filters every table, the rail counts the matches. Nothing
  // is selected, the picture is about the tables and the rail.
  await report.getByTestId("inspector-close").click();
  await expect(report.getByTestId("inspector")).toHaveCount(0);
  await report.getByTestId("search-input").fill("laci");
  await expect(report.getByTestId("rail-count-Species")).toContainText("/");
  await restPointer(report);
  const filled = Math.max(
    await contentBottom(report.getByTestId("type-rail")),
    await contentBottom(report.getByTestId("tables")),
  );
  await shot("report-search", report, {
    clip: { x: 0, y: 0, width: REPORT_VIEWPORT.width, height: Math.ceil(filled) + 16 },
  });
  await report.close();

  // report-overview.png: the report with an element selected, so that the rail, the tables and
  // the inspector all show at once. The tables start at the species, whose first row is the
  // selected one.
  const overview = await newPage(REPORT_VIEWPORT, inspector);
  await open(overview, "BIOMD0000000012");
  await selectRow(overview, overview.getByTestId("table-Species"), "PX");
  await expect(overview.getByTestId("attributes-column")).toBeVisible();
  await scrollToSection(overview, "Species");
  await restPointer(overview);
  await shot("report-overview", overview);
  await overview.close();

  // the parts of the report which are read on their own, in a window wide enough for them to be
  // captured at the width of the article column
  const parts = await newPage(WIDE_VIEWPORT);

  // inspector-annotations.png: an element with resolved annotation labels. icg_body carries an
  // indocyanine green species whose SBO, CHEBI and NCIt resources resolve to a name (the
  // InChIKey resource has no label to resolve to, and stays a plain link).
  await open(parts, "icg_body (icg_body.xml)");
  await parts.getByTestId("search-input").fill("Cre_plasma_icg");
  await selectRow(parts, parts.getByTestId("table-Species"), "Cre_plasma_icg");
  const annotationsColumn = parts.getByTestId("annotations-column");
  // every resource which resolves has to carry its label before the shot is taken, otherwise a
  // rerun catches a different set of answers and produces a different image. An unresolved
  // resource shows the resource itself as the text of its link.
  for (const resource of [
    "https://identifiers.org/SBO:0000247",
    "https://identifiers.org/CHEBI:31696",
    "https://identifiers.org/ncit/C65913",
  ]) {
    await expect(annotationsColumn.locator(`a[href="${resource}"]`)).not.toHaveText(resource);
  }
  await expect(
    annotationsColumn.locator('a[href="https://identifiers.org/CHEBI:31696"]'),
  ).toHaveText("indocyanine green");
  await restPointer(parts);
  // the annotations of the column alone: its notes and history follow below the visible area of
  // the panel, where they would be cut off in the middle of a line
  await shotFitted("inspector-annotations", parts, annotationsColumn.locator("section").first());

  // archive-entries.png: the bar of a COMBINE archive report, cropped to the part which names
  // the entry, the model, the level and version and the packages of the document. The entries
  // themselves are in the list the select opens, which the browser draws outside the page,
  // where no screenshot of the page reaches it.
  await open(parts, "CompModels");
  await expect(parts.getByTestId("entry-select")).toBeVisible();
  await restPointer(parts);
  const bar = await parts.getByTestId("app-bar").boundingBox();
  await shot("archive-entries", parts, {
    clip: { x: bar.x, y: bar.y, width: COLUMN_WIDTH, height: bar.height },
  });
  await parts.close();
} finally {
  // a failed expectation must not leave a chromium process behind
  await browser.close();
}
