import type { ValidationIssue } from "@/api/types";

export type Severity = ValidationIssue["severity"];

/** The severities from the worst to the mildest, the order of every list of issues. */
export const SEVERITY_ORDER: readonly Severity[] = ["error", "warning", "info"];

const RANK: Record<Severity, number> = { error: 0, warning: 1, info: 2 };

/** The worse of two severities, where null is no issue at all. */
export function worse(a: Severity | null, b: Severity): Severity {
  return a === null || RANK[b] < RANK[a] ? b : a;
}

/** The issues sorted errors first, in their order otherwise. */
export function bySeverity(issues: readonly ValidationIssue[]): ValidationIssue[] {
  return [...issues].sort((a, b) => RANK[a.severity] - RANK[b.severity]);
}

/** The issues of one rule: the list of all issues shows a rule once, with its elements. */
export interface IssueGroup {
  rule: number;
  severity: Severity;
  category: string;
  shortMessage: string;
  issues: ValidationIssue[];
}

/** The issues grouped by rule, errors first, then by the number of the rule. */
export function groupByRule(issues: readonly ValidationIssue[]): IssueGroup[] {
  const groups = new Map<number, IssueGroup>();
  for (const issue of issues) {
    const group = groups.get(issue.rule);
    if (group) {
      group.issues.push(issue);
      group.severity = worse(group.severity, issue.severity);
    } else {
      groups.set(issue.rule, {
        rule: issue.rule,
        severity: issue.severity,
        category: issue.category,
        shortMessage: issue.shortMessage,
        issues: [issue],
      });
    }
  }
  return [...groups.values()].sort(
    (a, b) => RANK[a.severity] - RANK[b.severity] || a.rule - b.rule,
  );
}
