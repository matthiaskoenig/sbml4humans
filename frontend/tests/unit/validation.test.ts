import { describe, expect, it } from "vitest";

import type { ValidationIssue } from "@/api/types";
import { groupByRule, worse } from "@/report/validation";

function issue(rule: number, severity: ValidationIssue["severity"], pk: string): ValidationIssue {
  return {
    rule,
    severity,
    category: "c",
    shortMessage: `m${rule}`,
    message: "",
    line: 1,
    column: 1,
    pk,
  };
}

describe("validation", () => {
  it("groups by rule, errors first", () => {
    const groups = groupByRule([
      issue(20513, "warning", "a"),
      issue(10601, "error", "b"),
      issue(20513, "warning", "c"),
      issue(99505, "warning", "d"),
    ]);
    expect(groups.map((g) => g.rule)).toEqual([10601, 20513, 99505]);
    expect(groups[1]?.issues.map((i) => i.pk)).toEqual(["a", "c"]);
  });

  it("keeps hundreds of issues of one rule to one group", () => {
    const many = Array.from({ length: 435 }, (_, k) => issue(99508, "warning", `p${k}`));
    expect(groupByRule(many)).toHaveLength(1);
  });

  it("orders severities", () => {
    expect(worse(null, "info")).toBe("info");
    expect(worse("warning", "error")).toBe("error");
    expect(worse("error", "warning")).toBe("error");
  });
});
