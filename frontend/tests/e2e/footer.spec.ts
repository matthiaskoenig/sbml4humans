import { expect, test, type Page } from "@playwright/test";

import { openExample, REPRESSILATOR_FILE } from "./helpers";

const REPOSITORY_URL = "https://github.com/matthiaskoenig/sbml4humans";

// `VITE_DOCS_URL` of `.env.development`, which the dev server of the tests reads
const DOCS_URL = "https://matthiaskoenig.github.io/sbml4humans/";

/** The footer with the links which say who made the application and how to cite it. */
async function expectFooterLinks(page: Page): Promise<void> {
  const footer = page.getByTestId("app-footer");
  await expect(footer).toBeVisible();
  await expect(footer).toContainText("© 2021-2026 Matthias König");
  await expect(footer.getByTestId("footer-github")).toHaveAttribute("href", REPOSITORY_URL);
  await expect(footer.getByTestId("footer-lab")).toHaveAttribute(
    "href",
    "https://livermetabolism.com",
  );
  await expect(footer.getByTestId("footer-doi")).toHaveAttribute(
    "href",
    "https://doi.org/10.5281/zenodo.22827237",
  );
  await expect(footer.getByTestId("footer-docs")).toHaveAttribute("href", DOCS_URL);
  await expect(footer.getByTestId("footer-cite")).toHaveAttribute(
    "href",
    `${DOCS_URL}#how-to-cite`,
  );
  await expect(footer.getByTestId("footer-privacy")).toHaveAttribute(
    "href",
    `${REPOSITORY_URL}/blob/main/frontend/privacy_notice.md`,
  );
}

test("the home page says which build it is and how to cite it", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("home-page")).toBeVisible();
  await expectFooterLinks(page);
  // the development build runs from the repository, so it knows its commit
  const footer = page.getByTestId("app-footer");
  await expect(footer).toContainText(/SBML4Humans \d+\.\d+\.\d+ \([0-9a-f]{7}\)/);
  // the version is the link to its release on GitHub, whose body are the release notes
  const release = footer.getByTestId("footer-release");
  await expect(release).toHaveText(/^\d+\.\d+\.\d+$/);
  await expect(release).toHaveAttribute(
    "href",
    new RegExp(`^${REPOSITORY_URL}/releases/tag/\\d+\\.\\d+\\.\\d+$`),
  );
  const commit = footer.getByTestId("footer-commit");
  await expect(commit).toHaveAttribute(
    "href",
    new RegExp(`^${REPOSITORY_URL}/commit/[0-9a-f]{40}$`),
  );
  await expect(commit).toHaveText(/^[0-9a-f]{7}$/);
});

test("the examples page carries the same footer", async ({ page }) => {
  await page.goto("/examples");
  await expect(page.getByTestId("examples-grid")).toBeVisible();
  await expectFooterLinks(page);
});

test("the report page carries the same footer under its split", async ({ page }) => {
  await openExample(page, "BIOMD0000000012");
  await expectFooterLinks(page);
  // the page is a full height workspace: the footer is the last thing in the window and the
  // window itself does not scroll
  const element = page.getByTestId("app-footer");
  const footer = (await element.boundingBox())!;
  const viewport = page.viewportSize()!;
  expect(Math.round(footer.y + footer.height)).toBe(viewport.height);
  const pageHeight = await element.evaluate(
    (node) => node.ownerDocument.documentElement.scrollHeight,
  );
  expect(pageHeight).toBe(viewport.height);
});

test("the feedback link of the bar opens an issue which names the build and the report", async ({
  page,
}) => {
  await openExample(page, "BIOMD0000000012");
  await page.getByTestId("table-Species").locator("tbody tr[data-pk]").first().click();
  const link = page.getByTestId("app-bar-feedback");
  await expect(link).toHaveText("Feedback");
  await expect(link).toHaveAttribute("target", "_blank");
  const href = (await link.getAttribute("href"))!;
  expect(href.startsWith(`${REPOSITORY_URL}/issues/new?body=`)).toBe(true);
  const body = new URL(href).searchParams.get("body")!;
  expect(body).toMatch(/- SBML4Humans \d+\.\d+\.\d+ \([0-9a-f]{7}\)/);
  expect(body).toContain("- model: the example `BIOMD0000000012`");
  // the view of the report is part of the page, so a maintainer opens what the reader saw
  expect(body).toMatch(/- page: `\/examples\/BIOMD0000000012\?pk=.*Species.*`/);
});

test("the feedback of an uploaded file names neither the file nor its elements", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByTestId("file-input").setInputFiles(REPRESSILATOR_FILE);
  await expect(page.getByTestId("report-page")).toBeVisible();
  await expect(page).toHaveURL(/pk=/);
  const href = (await page.getByTestId("app-bar-feedback").getAttribute("href"))!;
  const body = new URL(href).searchParams.get("body")!;
  expect(body).toContain("- page: `/report`");
  expect(body).toContain("- model: a file of my own");
  expect(body).not.toContain("BIOMD0000000012");
});
