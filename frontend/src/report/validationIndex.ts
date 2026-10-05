import type { ElementType, EntryValidation, ValidationIssue } from "@/api/types";
import type { ReportIndex } from "@/report/index";
import { bySeverity, worse, type Severity } from "@/report/validation";

export type SkipReason = NonNullable<EntryValidation["skipped"]>;

function push<K, V>(map: Map<K, V[]>, key: K, value: V): void {
  const list = map.get(key);
  if (list) list.push(value);
  else map.set(key, [value]);
}

/** Lookups over the validation of one entry: the issues by element, the issues an element of a
 * table holds through the elements without a row of their own (`ReportIndex.holderOf`) and the
 * worst severity of a row and of a type. The validation is answered apart from the report and may
 * concern a pk the report does not hold (the local server reads the file again): such an issue is
 * counted and listed and marks no row. */
export class ValidationIndex {
  readonly report: ReportIndex;
  /** The issues of the validation of the document, in the order of libsbml. */
  readonly issues: readonly ValidationIssue[];
  /** Why the consistency of the document was not checked, null where it was: its issues are then
   * those of reading it alone, or none. */
  readonly skipped: SkipReason | null;
  /** The number of issues of each severity. */
  readonly issueCounts: Record<Severity, number> = { error: 0, warning: 0, info: 0 };
  private readonly issuesByPk = new Map<string, ValidationIssue[]>();
  private readonly worstByPk = new Map<string, Severity>();
  /** The issues of the nested elements without a row, by the pk of the row which holds them. */
  private readonly heldByPk = new Map<string, ValidationIssue[]>();

  constructor(report: ReportIndex, validation: EntryValidation) {
    this.report = report;
    this.issues = validation.issues;
    this.skipped = validation.skipped;
    for (const issue of this.issues) {
      push(this.issuesByPk, issue.pk, issue);
      // the issue of an element without a row marks the row which holds it
      const row = report.holderOf(issue.pk);
      if (row) push(this.heldByPk, row, issue);
      for (const marked of row ? [issue.pk, row] : [issue.pk]) {
        this.worstByPk.set(marked, worse(this.worstByPk.get(marked) ?? null, issue.severity));
      }
      this.issueCounts[issue.severity] += 1;
    }
  }

  /** The issues of an element, errors first. */
  issuesOf(pk: string): ValidationIssue[] {
    return bySeverity(this.issuesByPk.get(pk) ?? []);
  }

  /** The issues of the elements an element of a table holds which have no row of their own, the
   * kinetic law of a reaction or the trigger of an event, errors first; each names its element by
   * its pk. Empty for every element which is no row of a table. */
  heldIssuesOf(pk: string): ValidationIssue[] {
    return bySeverity(this.heldByPk.get(pk) ?? []);
  }

  /** The issues of an element and of those it holds (`heldIssuesOf`), errors first: the issues
   * of its row, its tooltip and its inspector. */
  rowIssuesOf(pk: string): ValidationIssue[] {
    return bySeverity([...(this.issuesByPk.get(pk) ?? []), ...(this.heldByPk.get(pk) ?? [])]);
  }

  /** The worst severity of the issues of an element and of those it holds (`heldIssuesOf`), null
   * without one: the mark of its row. */
  worstSeverity(pk: string): Severity | null {
    return this.worstByPk.get(pk) ?? null;
  }

  /** The worst severity of the elements of a type in one model: the type bar and the tables
   * show one model, and an issue of another model is not theirs. */
  worstSeverityOfType(type: ElementType, modelId: string): Severity | null {
    let worst: Severity | null = null;
    for (const element of this.report.byType(modelId).get(type) ?? []) {
      const severity = this.worstByPk.get(element.pk);
      if (severity) worst = worse(worst, severity);
    }
    return worst;
  }
}
