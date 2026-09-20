// Screenshots of the application for the documentation, written to docs/images/ and shown by
// docs/index.md, docs/inputs.md and docs/report.md.
// Usage: start the backend (cd backend && uv run uvicorn sbml4humans.api:api --port 1444) and
// the dev server (cd frontend && npx vite --port 3456), then `npm run screenshots`. Rerun it
// after a change of the user interface, the images are committed alongside the documentation.
//
// The article column of the built site is at most COLUMN_WIDTH wide and shows an image at the
// width of the column, since every picture here is taken at twice the device scale and carries
// more pixels than that. A page and a part of the report are therefore captured exactly that
// wide, which is what draws their text at the size of the text next to them. The report as a
// whole needs its type bar, its tables and its inspector at once, which no window that narrow
// shows: it is captured in REPORT_VIEWPORT, the narrowest window in which the layout is honest,
// and the documentation links those images to their file, so that a click opens them at full
// size. The tables of a qualitative model are captured at the width of the column, which every
// one of them fits.
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
// the window the report as a whole is captured in: the narrowest one in which the bar states the
// search, the model, the level and the packages of a report next to each other, the inspector
// opens at a third of it without breaking a value such as `SBO:0000252` inside the token, and the
// tables keep the columns of a species left of it. The height is the one the pictures aim at,
// they end a few pixels above or below it, where no pane is cut through a line.
const REPORT_VIEWPORT = { width: 1200, height: 800 };
// the width the inspector is dragged to for the pictures of the inspector alone: the article
// column, so that its text is the size of the text next to it. It stays one column of three
// sections below `@4xl`, which is what a reader of a report sees. A section of it is the 24 px of
// its padding narrower and is shown a breath larger than the panel around it.
const INSPECTOR_WIDTH = COLUMN_WIDTH;
// the window the parts of the report are captured in. It is taller than any of them, the picture
// of the inspector shrinks it to the height its three sections need.
const PARTS_VIEWPORT = { width: 1200, height: 1600 };
// how much of the report is left around the help dialog: the dialog is painted over the report,
// which its backdrop darkens, and this much of it says so in the picture
const HELP_MARGIN = 40;
// the window the strip of the app bar is captured in: wide enough for a strip of COLUMN_WIDTH
// which starts at the context of the report to end before the links at the right of the bar
const ARCHIVE_WIDTH = 1600;

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
  /** A page of the given window size. A width remembers the inspector the way a real drag of the
   * divider remembers it, without one the inspector opens at the third of the window it opens at
   * for a reader who has never dragged it. */
  async function newPage(viewport, inspectorWidth = null) {
    const page = await browser.newPage({ viewport, deviceScaleFactor: 2 });
    if (inspectorWidth !== null) {
      await page.addInitScript(
        (width) => localStorage.setItem("sbml4humans.split.inspector-width", String(width)),
        inspectorWidth,
      );
    }
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
   * measured, since a container such as a pane of the split is exactly the box that lies about
   * the content it holds. */
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

  /** Screenshots `locator` cropped to its content instead of to its full box: the inspector is a
   * pane of the split and fills the height of the window, so its own box reaches well past its
   * content. */
  async function shotFitted(name, page, locator) {
    const box = await locator.boundingBox();
    const height = Math.min(Math.ceil((await contentBottom(locator)) - box.y) + 16, box.height);
    await shot(name, page, { clip: { x: box.x, y: box.y, width: box.width, height } });
  }

  /** Screenshots the open help dialog of `page` with HELP_MARGIN of the report around it. The
   * dialog is centred in the window and narrower than it, so the margin holds the report the
   * dialog was opened from, and the clip is kept inside the window where the dialog is as tall
   * as the window allows it to be. */
  async function shotDialog(name, page) {
    const box = await page.getByTestId("help-dialog").boundingBox();
    const view = page.viewportSize();
    const x = Math.max(0, box.x - HELP_MARGIN);
    const y = Math.max(0, box.y - HELP_MARGIN);
    await shot(name, page, {
      clip: {
        x,
        y,
        width: Math.min(box.width + 2 * HELP_MARGIN, view.width - x),
        height: Math.min(box.height + 2 * HELP_MARGIN, view.height - y),
      },
    });
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

  /** Closes the inspector a report opens with, for a picture of the tables alone. */
  async function closeInspector(page) {
    await page.getByTestId("inspector-close").click();
    await expect(page.getByTestId("inspector")).toHaveCount(0);
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

  /** Waits for the label of the SBO term of the species `PX` of the repressilator, which is
   * resolved in a request of its own: the height of the annotations depends on it, and without
   * the wait the picture and the height of the window below differ from run to run. */
  function resolvedSboTerm(page) {
    return expect(
      page
        .getByTestId("annotations-column")
        .locator('a[href="https://identifiers.org/SBO:0000252"]'),
    ).toHaveText("polypeptide chain");
  }

  /** The height of everything the report page shows above and below its two panes: the app bar,
   * the type bar and the footer. */
  async function chromeHeight(page) {
    const pane = await page.getByTestId("tables").boundingBox();
    return page.viewportSize().height - pane.height;
  }

  /** How much of the inspector the window does not show, in px. */
  function inspectorOverflow(page) {
    return page
      .getByTestId("inspector-body")
      .evaluate(
        (body) => body.firstElementChild.scrollHeight - body.firstElementChild.clientHeight,
      );
  }

  /** Grows the window to the height at which the three sections of the inspector neither scroll
   * nor stretch. The panel is a pane of the split: in a taller window it stretches its sections
   * and a picture of it ends in the empty space of that stretch, in a shorter one it scrolls them
   * and the picture cuts the last. The window starts too short on purpose, and what the sections
   * then overflow is exactly what it is missing. */
  async function fitInspector(page, height = 500) {
    const width = page.viewportSize().width;
    await page.setViewportSize({ width, height });
    const overflow = await inspectorOverflow(page);
    if (overflow <= 0) throw new Error(`the inspector already fits a window of ${height} px`);
    await page.setViewportSize({ width, height: height + Math.ceil(overflow) });
    await expect.poll(() => inspectorOverflow(page)).toBeLessThanOrEqual(0);
  }

  /** Fails, naming them, when a table of the page is wider than the pane it is in. Such a table
   * scrolls inside its section for a reader, which a picture cannot show and which reads as a
   * picture that was cropped too narrow. */
  async function tablesFit(page) {
    const wider = await page
      .getByTestId("tables")
      .evaluate((pane) =>
        [...pane.querySelectorAll("[data-testid^='table-']")]
          .filter((table) => table.scrollWidth > table.clientWidth)
          .map((table) => table.dataset.testid),
      );
    if (wider.length > 0) {
      throw new Error(`wider than the window they are in: ${wider.join(", ")}`);
    }
  }

  /** The heights at which the tables can be cut without cutting a row in half, measured from the
   * top of the visible part of the pane: the bottom of every row and of every section. A picture
   * which ends in the upper pixels of a row is read as a rendering fault rather than as the edge
   * of the picture. */
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

  /** The lines of the open inspector, measured from the top of the pane it shares with the
   * tables: the box of every leaf, grown by the padding around it. A height which crosses none of
   * them ends the picture between two lines of the inspector as well. */
  function inspectorLines(page) {
    return page.getByTestId("inspector").evaluate((panel) => {
      const top = panel.getBoundingClientRect().top;
      const margin = 6;
      return [...panel.querySelectorAll("*")]
        .filter((node) => node.children.length === 0)
        .map((node) => node.getBoundingClientRect())
        .filter((box) => box.height > 0)
        .map((box) => [box.top - top - margin, box.bottom - top + margin]);
    });
  }

  /** The height of the two panes of the report which is closest to `target` and cuts neither of
   * them through a line: a row of the tables ends there and no line of the inspector crosses it.
   * The inspector of an element is taller than any honest window, it scrolls in the picture as it
   * scrolls for a reader, and this is where the picture lets it end. */
  async function paneHeight(page, target) {
    const lines = await inspectorLines(page);
    const cuts = (await cutPoints(page)).filter((cut) =>
      lines.every(([top, bottom]) => cut <= top || cut >= bottom),
    );
    if (cuts.length === 0) throw new Error("no height cuts both panes between their lines");
    return cuts.reduce((best, cut) =>
      Math.abs(cut - target) < Math.abs(best - target) ? cut : best,
    );
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
  // examples (101 at the time of writing), far taller than any window, so the picture ends below
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

  // the report as a whole: the type bar on top, the element tables and the inspector next to each
  // other below it, the footer under both
  const report = await newPage(REPORT_VIEWPORT);

  // report-tables.png: the repressilator report with nothing selected, so the tables have the
  // whole width of the window and no inspector shows; a report opens with its model selected, so
  // the inspector is closed first. The picture is the top of the page, it ends between two rows
  // of the tables instead of at the footer below them.
  await open(report, "BIOMD0000000012");
  await closeInspector(report);
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

  // report-search.png: the search box filters every table, the type bar counts the matches.
  // Nothing is selected, the picture is about the tables and the bar.
  await report.getByTestId("search-input").fill("laci");
  await expect(report.getByTestId("bar-count-Species")).toContainText("/");
  await restPointer(report);
  const filled = Math.max(
    await contentBottom(report.getByTestId("type-bar")),
    await contentBottom(report.getByTestId("tables")),
  );
  await shot("report-search", report, {
    clip: { x: 0, y: 0, width: REPORT_VIEWPORT.width, height: Math.ceil(filled) + 16 },
  });

  await report.close();

  // report-qual.png: the report of a qualitative model, the one kind of model which is built
  // from no reaction at all. Its two tables are the state space of the model and its influence
  // graph, which is what the columns of a qualitative report are for, and nothing is selected so
  // that both tables have the whole width of the window. The signs of the influences are the
  // point of the picture, so it is taken in a window as wide as the column of the site, where
  // they are drawn at the size of the text next to them, from the type bar down: every table of
  // the model fits that width, and the app bar above them does not.
  const qual = await newPage(PAGE_VIEWPORT);
  await open(qual, "qual_example (qual_example.xml)");
  await closeInspector(qual);
  await expect(qual.getByTestId("table-QualitativeSpecies")).toBeVisible();
  await expect(qual.getByTestId("table-Transition")).toBeVisible();
  await tablesFit(qual);
  const typeBar = await qual.getByTestId("type-bar").boundingBox();
  const qualTables = await qual.getByTestId("tables").boundingBox();
  await restPointer(qual);
  await shot("report-qual", qual, {
    clip: {
      x: 0,
      y: typeBar.y,
      width: qual.viewportSize().width,
      height: qualTables.y - typeBar.y + (await cutWithin(qual, qualTables.height)),
    },
  });
  await qual.close();

  // report-overview.png: the whole page with an element selected, the type bar, the tables, the
  // inspector of the selected species and the footer. The tables start at the species, whose
  // first row is the selected one, and the window is as high as the two panes need to end
  // between two lines.
  const overview = await newPage(REPORT_VIEWPORT);
  await open(overview, "BIOMD0000000012");
  await selectRow(overview, overview.getByTestId("table-Species"), "PX");
  await expect(overview.getByTestId("attributes-column")).toBeVisible();
  await resolvedSboTerm(overview);
  await scrollToSection(overview, "Species");
  const chrome = await chromeHeight(overview);
  const height = await paneHeight(overview, REPORT_VIEWPORT.height - chrome);
  await overview.setViewportSize({
    width: REPORT_VIEWPORT.width,
    height: Math.round(height + chrome),
  });
  await scrollToSection(overview, "Species");
  await restPointer(overview);
  await shot("report-overview", overview);
  await overview.close();

  // the explanations, in the window a report is read in: what the dialog covers is a report with
  // an element in its inspector, which is where the labels that open it are
  const help = await newPage(REPORT_VIEWPORT);
  await open(help, "BIOMD0000000012");
  await selectRow(help, help.getByTestId("table-Species"), "PX");
  await expect(help.getByTestId("attributes-column")).toBeVisible();

  // help-dialog.png: the explanation of one attribute, opened by a click on the label of the row
  // which shows it. The entry of an attribute carries every part of the dialog at once: the
  // breadcrumb of the type it belongs to, the badges of its data type and of whether the
  // specification requires it, the summary, the overview, the technical list, the validation
  // rules of the specification and the link into the documentation.
  await help.getByTestId("attributes-column").getByText("initialAmount", { exact: true }).click();
  // the rendered description is the last part of the dialog to arrive, behind the import of the
  // markdown renderer, and the dialog grows by its height: without the wait the picture is
  // measured for a dialog which is a paragraph shorter than the one it captures
  await expect(help.getByTestId("help-markdown")).toBeVisible();
  await expect(help.getByTestId("help-rules")).toBeVisible();
  await restPointer(help);
  await shotDialog("help-dialog", help);

  // help-type.png: the explanation of a type, reached from the attribute by its breadcrumb. A
  // type lists its attributes, each of them a row which opens it, and the last row leads to the
  // attributes every element carries. The description and the rules of a type fill the dialog, so
  // the body is scrolled to the heading of that table.
  await help.getByTestId("help-owner").click();
  await expect(help.getByTestId("help-attributes")).toBeVisible();
  await help.getByTestId("help-body").evaluate((body) => {
    const attributes = body.querySelector('[data-testid="help-attributes"]');
    // the heading of the table stands 8 px below the top of the body, the rest of the margin
    // which parts it from the section above it is scrolled away with that section
    body.scrollTop += attributes.getBoundingClientRect().top - body.getBoundingClientRect().top - 8;
  });
  await restPointer(help);
  await shotDialog("help-type", help);
  await help.close();

  // the parts of the report which are read on their own, with the inspector dragged to the width
  // of the article column and a window which holds all of it
  const parts = await newPage(PARTS_VIEWPORT, INSPECTOR_WIDTH);

  // inspector-species.png: the inspector of a species alone, its three sections one under the
  // other in the column the inspector is. The window is shrunk to the height the sections need,
  // which is the height at which they neither scroll nor stretch.
  await open(parts, "BIOMD0000000012");
  await selectRow(parts, parts.getByTestId("table-Species"), "PX");
  await expect(parts.getByTestId("attributes-column")).toBeVisible();
  await resolvedSboTerm(parts);
  await fitInspector(parts);
  await restPointer(parts);
  await shotFitted("inspector-species", parts, parts.getByTestId("inspector"));
  await parts.setViewportSize(PARTS_VIEWPORT);

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
  // the annotations of the section alone: the notes and the history follow below it, and the
  // section is scrolled into view of the panel before it is captured
  const annotations = annotationsColumn.locator("section").first();
  await annotations.scrollIntoViewIfNeeded();
  await shot("inspector-annotations", annotations);

  // inspector-gene-association.png: the attributes of a reaction of a constraint based model, the
  // rows a reader of such a model comes for: the equation, the two flux bounds and the genes the
  // reaction needs as the expression their tree stands for. R_CYTBD of the E. coli core model is
  // an `or` of two `and` groups, the two complexes which each catalyse it, which is the shape of
  // an association and still one line. The window is grown until the three sections of the
  // inspector neither scroll nor stretch, so that the attributes are not cut by the pane, and
  // the picture is the inspector from its header to the end of its attributes, which is what
  // tells it from a table of the page.
  await open(parts, "e_coli_core (e_coli_core.xml.gz)");
  await parts.getByTestId("search-input").fill("R_CYTBD");
  await selectRow(parts, parts.getByTestId("table-Reaction"), "R_CYTBD");
  await expect(parts.getByTestId("attributes-column")).toBeVisible();
  await fitInspector(parts);
  await restPointer(parts);
  const inspector = await parts.getByTestId("inspector").boundingBox();
  // the section of the attributes ends 0.75rem below its content
  const attributesEnd = (await contentBottom(parts.getByTestId("attributes-column"))) + 12;
  await shot("inspector-gene-association", parts, {
    clip: {
      x: inspector.x,
      y: inspector.y,
      width: inspector.width,
      height: Math.ceil(attributesEnd - inspector.y),
    },
  });

  // inspector-external-model.png: a species of a comp model whose replaced element ends in
  // another entry of the archive, the link carrying the file name of that entry. The entry is
  // named in the address, since the archive marks no master entry and opens on either one.
  await parts.goto(
    `${BASE_URL}/examples/CompModels?entry=${encodeURIComponent("./models/omex_comp.xml")}`,
  );
  await expect(parts.getByTestId("report-page")).toBeVisible();
  await selectRow(parts, parts.getByTestId("table-Species"), "S0");
  await expect(parts.getByTestId("element-link-entry").first()).toBeVisible();
  await fitInspector(parts);
  await restPointer(parts);
  await shotFitted("inspector-external-model", parts, parts.getByTestId("inspector"));
  await parts.setViewportSize(PARTS_VIEWPORT);

  // archive-entries.png: the context of a COMBINE archive report in the app bar, a strip of the
  // bar from the select of the entries on, as wide as the article column. The bar from the logo
  // on is wider than that since the search box sits between the logo and the context, and the
  // search is in the pictures of the whole report anyway. The entries themselves are in the list
  // the select opens, which the browser draws outside the page, where no screenshot of the page
  // reaches it.
  await parts.setViewportSize({ width: ARCHIVE_WIDTH, height: PARTS_VIEWPORT.height });
  await open(parts, "CompModels");
  await expect(parts.getByTestId("entry-select")).toBeVisible();
  await restPointer(parts);
  const bar = await parts.getByTestId("app-bar").boundingBox();
  const select = await parts.getByTestId("entry-select").boundingBox();
  const links = await parts.getByTestId("app-bar-docs").boundingBox();
  const strip = { x: select.x - 12, width: COLUMN_WIDTH };
  if (strip.x + strip.width > links.x) {
    throw new Error(`the strip of the bar reaches the links of ${ARCHIVE_WIDTH} px window`);
  }
  await shot("archive-entries", parts, { clip: { ...strip, y: bar.y, height: bar.height } });
  await parts.close();
} finally {
  // a failed expectation must not leave a chromium process behind
  await browser.close();
}
