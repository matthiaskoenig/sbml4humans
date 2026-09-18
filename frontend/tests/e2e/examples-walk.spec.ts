import { expect, test } from "@playwright/test";

import { openExample } from "./helpers";

// The `examples-walk` project of `playwright.config.ts` runs this spec alone, after the other
// specs: it opens every example, and creating a report is CPU bound in the backend, so sharing
// the backend with the parallel workers of the other specs makes the reports arrive late.
// Every example gets two minutes: the largest one, Recon3D, is a 75 MB gzipped model whose
// report creation, transfer and indexing take far longer than the configured expect timeout on
// a two core CI runner.
test("every example renders its sections", async ({ page, request }) => {
  const response = await request.get("http://localhost:1444/api/examples");
  const { examples } = (await response.json()) as { examples: { id: string }[] };
  test.setTimeout(examples.length * 15_000);
  for (const example of examples) {
    await openExample(page, example.id, 120_000);
    await expect(page.getByTestId("type-bar")).toBeVisible();
    const sections = await page.locator("[data-testid^=section-]").count();
    // a model without any element renders the empty state instead of the sections
    if (sections === 0) await expect(page.getByTestId("no-matches"), example.id).toBeVisible();
    await expect(page.getByTestId("error-state"), example.id).toHaveCount(0);
  }
});
