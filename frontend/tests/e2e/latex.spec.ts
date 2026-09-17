import { expect, test } from "@playwright/test";

/** An assignment rule whose math sums TERM_COUNT `<ci>` terms: the backend turns it into 11,090
 * characters of LaTeX, well past MAX_LATEX_LENGTH, so the assignment rule table must show it as
 * text instead of rendering it with KaTeX. The backend's conversion of the math to LaTeX fails
 * for a flat sum of about 1,000 terms, which keeps the count below that. */
const TERM_COUNT = 800;
const parameters = Array.from(
  { length: TERM_COUNT },
  (_, i) => `<parameter id="x${i}" value="0" constant="false"/>`,
).join("\n      ");
const terms = Array.from({ length: TERM_COUNT }, (_, i) => `<ci> x${i} </ci>`).join(
  "\n            ",
);
const MODEL = `<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  <model id="big_sum_test" name="big sum test">
    <listOfParameters>
      <parameter id="y" value="0" constant="false"/>
      ${parameters}
    </listOfParameters>
    <listOfRules>
      <assignmentRule variable="y">
        <math xmlns="http://www.w3.org/1998/Math/MathML">
          <apply>
            <plus/>
            ${terms}
          </apply>
        </math>
      </assignmentRule>
    </listOfRules>
  </model>
</sbml>
`;

test("an assignment rule whose latex is too long to render shows text instead of KaTeX", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(MODEL);
  await page.getByTestId("paste-submit").click();
  await expect(page.getByTestId("report-page")).toBeVisible();

  const table = page.getByTestId("table-AssignmentRule");
  const row = table.locator("tbody tr[data-pk]").first();
  await expect(row.getByTestId("math-text")).toBeVisible();
  await expect(row.locator(".katex")).toHaveCount(0);
});
