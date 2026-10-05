import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";
import { ref } from "vue";

import { ApiError } from "@/api/client";
import ValidationSummary from "@/components/report/ValidationSummary.vue";
import { vTooltip } from "@/directives/tooltip";
import { ValidationIndexKey } from "@/report/context";
import { ReportIndex } from "@/report/index";
import { ValidationIndex } from "@/report/validationIndex";
import type { ValidationState } from "@/stores/report";
import { router } from "@/router";

import { loadReport, loadValidation, withIssues } from "./fixtures";

const validationReport = new ReportIndex(loadReport("validation"));
const validation = new ValidationIndex(validationReport, loadValidation("validation"));
// the repressilator carries unit warnings and no error, the constraint and event example none
const repressilatorReport = new ReportIndex(loadReport("repressilator"));
const repressilator = new ValidationIndex(repressilatorReport, loadValidation("repressilator"));
const constraintEvent = new ReportIndex(loadReport("constraint_event"));
const valid = new ValidationIndex(constraintEvent, withIssues([]));

let wrapper: ReturnType<typeof mount> | null = null;

function mountSummary(
  of: ValidationIndex | null,
  state: ValidationState | null = "done",
  error: ApiError | null = null,
  index: ReportIndex = of?.report ?? validationReport,
) {
  wrapper = mount(ValidationSummary, {
    props: { index, state, error },
    attachTo: document.body,
    global: {
      plugins: [router],
      directives: { tooltip: vTooltip },
      provide: { [ValidationIndexKey as symbol]: ref(of) },
    },
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
    expect(errors.text()).toBe("1 error");
    expect(errors.attributes("aria-label")).toBe("1 error");
    expect(errors.find("[data-testid=severity-error]").exists()).toBe(true);
    const warnings = summary.get("[data-testid=validation-warnings]");
    expect(warnings.text()).toBe(`${validation.issueCounts.warning} warnings`);
    expect(warnings.attributes("aria-label")).toBe(`${validation.issueCounts.warning} warnings`);
    expect(warnings.find("[data-testid=severity-warning]").exists()).toBe(true);
    expect(summary.find("[data-testid=validation-pending]").exists()).toBe(false);
  });

  it("selects the document, whose inspector lists the issues, on a click", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(validation);
    await summary.get("[data-testid=validation-errors]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(validationReport.document.pk);
  });

  it("leaves out the chip of a severity the document has no issue of", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(repressilator);
    expect(summary.find("[data-testid=validation-errors]").exists()).toBe(false);
    expect(summary.get("[data-testid=validation-warnings]").text()).toBe(
      `${repressilator.issueCounts.warning} warnings`,
    );
  });

  it("shows nothing for a document without errors and warnings", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(valid);
    expect(summary.find("[data-testid=validation-summary]").exists()).toBe(false);
    expect(summary.find("[data-testid=validation-pending]").exists()).toBe(false);
    expect(summary.find("[data-testid=validation-failed]").exists()).toBe(false);
  });

  it("says that a document which was not validated was not, and why, rather than nothing", async () => {
    await router.push({ path: "/report", query: {} });
    const tips = new Set<string>();
    for (const reason of [
      "expandedSize",
      "timeout",
      "memory",
      "crashed",
      "busy",
      "unanswered",
    ] as const) {
      const skipped = new ValidationIndex(constraintEvent, withIssues([], reason));
      const summary = mountSummary(skipped);
      const chip = summary.get("[data-testid=validation-skipped]");
      expect(chip.attributes("aria-label")).toBe("not validated");
      expect(chip.attributes("data-reason")).toBe(reason);
      await chip.trigger("mouseenter");
      tips.add(document.getElementById("app-tooltip")?.textContent ?? "");
      await chip.trigger("mouseleave");
      await chip.trigger("click");
      await flushPromises();
      expect(router.currentRoute.value.query.pk).toBe(constraintEvent.document.pk);
      summary.unmount();
      wrapper = null;
    }
    expect(tips.size).toBe(6);
    expect([...tips].find((tip) => tip.includes("busy"))).toContain("reload the report later");
  });

  it("asks to load a file or pasted content again when the server was busy", async () => {
    await router.push({ path: "/report", query: {} });
    const busy = new ValidationIndex(constraintEvent, withIssues([], "busy"), false);
    const summary = mountSummary(busy);
    const chip = summary.get("[data-testid=validation-skipped]");
    await chip.trigger("mouseenter");
    const tip = document.getElementById("app-tooltip")?.textContent ?? "";
    expect(tip).toContain("load it again later");
    expect(tip).not.toContain("reload");
  });

  it("shows a quiet chip while the validation is pending, and no counts", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(null, "pending");
    const chip = summary.get("[data-testid=validation-pending]");
    expect(chip.text()).toBe("validating");
    expect(chip.attributes("role")).toBe("status");
    expect(chip.find(".animate-spin").exists()).toBe(true);
    expect(summary.find("[data-testid=validation-summary]").exists()).toBe(false);
  });

  it("says that the validation failed, the message of the failure as its tooltip", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(
      null,
      "failed",
      new ApiError("The backend at /api is not reachable"),
    );
    const chip = summary.get("[data-testid=validation-failed]");
    expect(chip.text()).toBe("validation failed");
    expect(chip.attributes("aria-label")).toBe("validation failed");
    await chip.trigger("mouseenter");
    expect(document.getElementById("app-tooltip")?.textContent).toBe(
      "The backend at /api is not reachable",
    );
    expect(summary.find("[data-testid=validation-pending]").exists()).toBe(false);
    // the inspector of the document shows the failure with its details
    expect(chip.element.tagName).toBe("BUTTON");
    await chip.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.pk).toBe(validationReport.document.pk);
  });

  it("shows nothing without a report", async () => {
    await router.push({ path: "/report", query: {} });
    const summary = mountSummary(null, null);
    expect(summary.html()).not.toContain("data-testid");
  });
});
