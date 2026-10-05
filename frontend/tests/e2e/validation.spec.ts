import { expect, type Page, test } from "@playwright/test";

import { expectReport, openExample, query } from "./helpers";

const EXAMPLE = "validation (validation.xml)";

/** A comp document whose main model expands to `n` submodels on each of `depth` levels. */
function fanOut(depth: number, n: number): string {
  const submodels = (ref: string) =>
    "<comp:listOfSubmodels>" +
    Array.from(
      { length: n },
      (_, i) => `<comp:submodel comp:id="s${i}" comp:modelRef="${ref}"/>`,
    ).join("") +
    "</comp:listOfSubmodels>";
  const definitions = Array.from({ length: depth }, (_, k) =>
    k === 0
      ? '<comp:modelDefinition id="d0"/>'
      : `<comp:modelDefinition id="d${k}">${submodels(`d${k - 1}`)}</comp:modelDefinition>`,
  ).join("");
  return (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" ' +
    'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" ' +
    'level="3" version="1" comp:required="true">' +
    `<model id="m">${submodels(`d${depth - 1}`)}</model>` +
    `<comp:listOfModelDefinitions>${definitions}</comp:listOfModelDefinitions></sbml>`
  );
}

/** Wait until the validation, which is answered after the report, has arrived: its marks and
 * chips are complete only then, and an absent mark proves nothing before. */
async function expectValidated(page: Page): Promise<void> {
  await expect(page.getByTestId("validation-pending")).toHaveCount(0, { timeout: 30_000 });
}

/** Paste SBML on the home page and wait for its report. */
async function paste(page: Page, sbml: string): Promise<void> {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(sbml);
  await page.getByTestId("paste-submit").click();
  await expectReport(page);
}

/** The text of the tooltip of an element, which hovering it shows. */
async function tooltipOf(page: Page, testId: string): Promise<string> {
  await page.getByTestId(testId).hover();
  const tooltip = page.locator("#app-tooltip");
  await expect(tooltip).toBeVisible();
  return (await tooltip.textContent()) ?? "";
}

test.describe("validation", () => {
  test.beforeEach(async ({ page }) => {
    await openExample(page, EXAMPLE);
    await expectValidated(page);
  });

  test("leads from the summary over the list to an element and its issues", async ({ page }) => {
    const summary = page.getByTestId("validation-summary");
    await expect(summary.getByTestId("validation-errors")).toHaveText("1 error");
    await expect(summary.getByTestId("validation-errors")).toHaveAccessibleName("1 error");
    await expect(summary.getByTestId("validation-warnings")).toBeVisible();

    await summary.getByTestId("validation-errors").click();
    const inspector = page.getByTestId("inspector");
    await expect(inspector.getByTestId("inspector-type")).toHaveText("SBMLDocument");
    const groups = inspector.getByTestId("validation-list").getByTestId("validation-group");
    await expect(groups.first()).toContainText("10601");

    const compartment = groups.filter({ hasText: "10712" });
    await compartment.locator("summary").click();
    await compartment.getByTestId("element-link").first().click();
    await expect(inspector.getByTestId("inspector-type")).toHaveText("Compartment");
    await expect(inspector.getByTestId("inspector-validation")).toContainText("10712");
    await expect.poll(() => query(page, "pk")).toMatch(/Compartment:cell$/);

    // back returns to the list of the document
    await page.goBack();
    await expect(inspector.getByTestId("validation-list")).toBeVisible();
  });

  test("says that no issue matches filters which leave none", async ({ page }) => {
    await page.getByTestId("validation-errors").click();
    const list = page.getByTestId("inspector").getByTestId("validation-list");
    await list.getByTestId("validation-filter-error").uncheck();
    await list.getByTestId("validation-filter-warning").uncheck();
    await expect(list.getByTestId("validation-group")).toHaveCount(0);
    await expect(list.getByTestId("validation-no-match")).toHaveText(
      "No issues match the filters.",
    );
    await list.getByTestId("validation-filter-error").check();
    await expect(list.getByTestId("validation-no-match")).toHaveCount(0);
    await expect(list.getByTestId("validation-group")).toHaveCount(1);
  });

  test("names the issues of a row in its mark, which the keyboard passes over", async ({
    page,
  }) => {
    const row = page.locator('tbody tr[data-pk$="Parameter:k1"]');
    const mark = row.getByTestId("row-issue").getByRole("img");
    await expect(mark).toHaveAccessibleName(/^warning: .*10703/);
    // the row is the stop of the keyboard, the mark is none
    await row.focus();
    await page.keyboard.press("Tab");
    await expect(row.getByTestId("row-issue")).not.toBeFocused();
    await expect(mark).not.toBeFocused();
  });

  test("marks the rows and the types with issues", async ({ page }) => {
    await expect(
      page.locator('tbody tr[data-pk$="Parameter:k1"]').getByTestId("row-issue"),
    ).toBeVisible();
    await expect(
      page.locator('tbody tr[data-pk$="Species:A"]').getByTestId("row-issue"),
    ).toHaveCount(0);
    await expect(
      page.getByTestId("bar-type-Parameter").getByTestId("severity-warning"),
    ).toBeVisible();
    // the reaction R1 has no issue of its own, the issue of its kinetic law marks its row
    await expect(
      page.locator('tbody tr[data-pk$="Reaction:R1"]').getByTestId("row-issue"),
    ).toBeVisible();
    await expect(
      page.getByTestId("bar-type-Reaction").getByTestId("severity-warning"),
    ).toBeVisible();
    // the error of the example is an issue of the model, whose entry of the type bar is its row
    await expect(page.getByTestId("bar-model").getByTestId("severity-error")).toBeVisible();
    await expect(page.getByTestId("bar-document").getByTestId("bar-issue-document")).toHaveCount(0);
  });
});

// these tests open documents of their own, not the validation example of the tests above
test.describe("the validation of other documents", () => {
  test("a document beyond the expanded size which is checked says it was not validated", async ({
    page,
  }) => {
    await paste(page, fanOut(5, 10));
    await expectValidated(page);

    const skipped = page.getByTestId("validation-summary").getByTestId("validation-skipped");
    await expect(skipped).toHaveText("not validated");
    await expect(skipped).toHaveAttribute("data-reason", "expandedSize");
    await expect(page.getByTestId("validation-errors")).toHaveCount(0);
    expect(await tooltipOf(page, "validation-skipped")).toContain("expand");
    await skipped.click();
    const list = page.getByTestId("inspector").getByTestId("validation-list");
    await expect(list.getByTestId("validation-skipped")).toHaveAttribute(
      "data-reason",
      "expandedSize",
    );
    await expect(list.getByTestId("validation-skipped")).toContainText(
      "Only the errors of reading the file are listed",
    );
    await expect(list.getByTestId("no-validation-issues")).toHaveCount(0);
  });

  test("a valid model shows no summary", async ({ page }) => {
    await openExample(page, "species (species.xml)");
    await expectValidated(page);
    await expect(page.getByTestId("validation-summary")).toHaveCount(0);
    await expect(page.getByTestId("validation-failed")).toHaveCount(0);
  });
});

test.describe("the validation answered after the report", () => {
  test("shows a quiet chip while it runs, then the counts and the marks", async ({ page }) => {
    // the validation answers when the test lets it, so that the pending state is observed
    let release!: () => void;
    const released = new Promise<void>((resolve) => (release = resolve));
    await page.route("**/api/validation/examples/**", async (route) => {
      await released;
      await route.continue();
    });
    await openExample(page, EXAMPLE);

    const pending = page.getByTestId("validation-pending");
    await expect(pending).toBeVisible();
    await expect(pending).toHaveAccessibleName("validating");
    await expect(pending).toHaveText("validating");
    // the report is there, its validation is not
    await expect(page.locator('tbody tr[data-pk$="Parameter:k1"]')).toBeVisible();
    await expect(page.getByTestId("validation-summary")).toHaveCount(0);
    await expect(page.getByTestId("row-issue")).toHaveCount(0);
    await expect(page.getByTestId("bar-model").getByTestId("severity-error")).toHaveCount(0);

    release();
    await expectValidated(page);
    await expect(page.getByTestId("validation-errors")).toHaveText("1 error");
    await expect(
      page.locator('tbody tr[data-pk$="Parameter:k1"]').getByTestId("row-issue"),
    ).toBeVisible();
    await expect(page.getByTestId("bar-model").getByTestId("severity-error")).toBeVisible();
  });

  test("a validation which failed says so, with its message", async ({ page }) => {
    const message = "the validation of the test failed";
    await page.route("**/api/validation/examples/**", (route) =>
      route.fulfill({ status: 200, json: { errors: [message], warnings: [], info: {} } }),
    );
    await openExample(page, EXAMPLE);

    const failed = page.getByTestId("validation-failed");
    await expect(failed).toHaveText("validation failed");
    await expect(failed).toHaveAccessibleName("validation failed");
    expect(await tooltipOf(page, "validation-failed")).toContain(message);
    // the report stays, without marks
    await expect(page.getByTestId("validation-summary")).toHaveCount(0);
    await expect(page.getByTestId("row-issue")).toHaveCount(0);
    await expect(page.locator('tbody tr[data-pk$="Parameter:k1"]')).toBeVisible();
  });

  test("a validation which failed shows its details in the inspector of the document", async ({
    page,
  }) => {
    await page.route("**/api/validation/examples/**", (route) =>
      route.fulfill({
        status: 200,
        json: {
          errors: ["the validation of the test failed", "Traceback (most recent call last)"],
          warnings: [],
          info: {},
        },
      }),
    );
    await openExample(page, EXAMPLE);

    await page.getByTestId("validation-failed").click();
    const failure = page.getByTestId("inspector").getByTestId("validation-failure");
    await expect(failure.getByTestId("validation-failure-message")).toContainText(
      "the validation of the test failed",
    );
    await expect(failure.getByTestId("validation-failure-traceback")).toHaveCount(0);
    await failure.getByTestId("validation-failure-toggle").click();
    await expect(failure.getByTestId("validation-failure-traceback")).toHaveText(
      "Traceback (most recent call last)",
    );
  });

  test("a validation the proxy refuses for its rate limit is busy", async ({ page }) => {
    // nginx answers a client beyond its limits with 429 and a page of its own
    await page.route("**/api/validation/examples/**", (route) =>
      route.fulfill({
        status: 429,
        contentType: "text/html",
        body: "<html><head><title>429 Too Many Requests</title></head></html>",
      }),
    );
    await openExample(page, EXAMPLE);

    const skipped = page.getByTestId("validation-summary").getByTestId("validation-skipped");
    await expect(skipped).toHaveAttribute("data-reason", "busy");
    await expect(page.getByTestId("validation-failed")).toHaveCount(0);
    expect(await tooltipOf(page, "validation-skipped")).toContain("reload the report later");
  });

  test("a check which crashed says that it ended abnormally", async ({ page }) => {
    await page.route("**/api/validation/examples/**", (route) =>
      route.fulfill({ status: 200, json: { entries: {}, skipped: "crashed" } }),
    );
    await openExample(page, EXAMPLE);

    const skipped = page.getByTestId("validation-summary").getByTestId("validation-skipped");
    await expect(skipped).toHaveAttribute("data-reason", "crashed");
    expect(await tooltipOf(page, "validation-skipped")).toContain("ended abnormally");
    await skipped.click();
    await expect(
      page
        .getByTestId("inspector")
        .getByTestId("validation-list")
        .getByTestId("validation-skipped"),
    ).toContainText("ended abnormally");
  });

  test("a busy server asks to reload the report of an example later", async ({ page }) => {
    await page.route("**/api/validation/examples/**", (route) =>
      route.fulfill({ status: 200, json: { entries: {}, skipped: "busy" } }),
    );
    await openExample(page, EXAMPLE);

    const skipped = page.getByTestId("validation-summary").getByTestId("validation-skipped");
    await expect(skipped).toHaveAttribute("data-reason", "busy");
    expect(await tooltipOf(page, "validation-skipped")).toContain("reload the report later");
    await skipped.click();
    const note = page
      .getByTestId("inspector")
      .getByTestId("validation-list")
      .getByTestId("validation-skipped");
    await expect(note).toHaveAttribute("data-reason", "busy");
    await expect(note).toContainText("Reload the report later");
  });

  test("a busy server asks to load pasted content again later", async ({ page }) => {
    await page.route("**/api/validation/content", (route) =>
      route.fulfill({ status: 200, json: { entries: {}, skipped: "busy" } }),
    );
    await paste(page, fanOut(1, 1));

    const skipped = page.getByTestId("validation-summary").getByTestId("validation-skipped");
    await expect(skipped).toHaveAttribute("data-reason", "busy");
    expect(await tooltipOf(page, "validation-skipped")).toContain("load it again later");
    await skipped.click();
    await expect(
      page
        .getByTestId("inspector")
        .getByTestId("validation-list")
        .getByTestId("validation-skipped"),
    ).toContainText("Load it again later");
  });
});
