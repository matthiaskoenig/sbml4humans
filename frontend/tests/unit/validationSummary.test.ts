import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import ValidationSummary from "@/components/report/ValidationSummary.vue";
import { vTooltip } from "@/directives/tooltip";
import { ReportIndex } from "@/report/index";
import { router } from "@/router";

import { loadReport } from "./fixtures";

const validation = new ReportIndex(loadReport("validation"));
// the repressilator carries unit warnings and no error, the constraint and event example none
const repressilator = new ReportIndex(loadReport("repressilator"));
const valid = new ReportIndex(loadReport("constraint_event"));

let wrapper: ReturnType<typeof mount> | null = null;

function mountSummary(index: ReportIndex) {
  wrapper = mount(ValidationSummary, {
    props: { index },
    global: { plugins: [router], directives: { tooltip: vTooltip } },
  });
  return wrapper;
}

afterEach(() => {
  wrapper?.unmount();
  wrapper = null;
});

describe("ValidationSummary", () => {
  it("counts the errors and the warnings of the document", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(validation);
    expect(summary.find("[data-testid=validation-summary]").exists()).toBe(true);
    const errors = summary.get("[data-testid=validation-errors]");
    expect(errors.text()).toBe("1error");
    expect(errors.find("[data-testid=severity-error]").exists()).toBe(true);
    const warnings = summary.get("[data-testid=validation-warnings]");
    expect(warnings.text()).toBe(`${validation.issueCounts.warning}warnings`);
    expect(warnings.find("[data-testid=severity-warning]").exists()).toBe(true);
  });

  it("selects the document, whose inspector lists the issues, on a click", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(validation);
    await summary.get("[data-testid=validation-errors]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(validation.document.pk);
  });

  it("leaves out the chip of a severity the document has no issue of", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(repressilator);
    expect(summary.find("[data-testid=validation-errors]").exists()).toBe(false);
    expect(summary.get("[data-testid=validation-warnings]").text()).toBe(
      `${repressilator.issueCounts.warning}warnings`,
    );
  });

  it("shows nothing for a document without errors and warnings", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(valid);
    expect(summary.find("[data-testid=validation-summary]").exists()).toBe(false);
  });
});
