import { expect, test, type Page } from "@playwright/test";

import { openExample } from "./helpers";

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

test("the report page is a full height workspace without a footer", async ({ page }) => {
  await openExample(page, "BIOMD0000000012");
  await expect(page.getByTestId("app-footer")).toHaveCount(0);
});
