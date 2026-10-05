import { describe, expect, it } from "vitest";

import type { Reaction } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { ValidationIndex } from "@/report/validationIndex";

import { loadReport, loadValidation, withIssues } from "./fixtures";

const validationReport = new ReportIndex(loadReport("validation"));
const validation = new ValidationIndex(validationReport, loadValidation("validation"));
const repressilatorReport = new ReportIndex(loadReport("repressilator"));
const repressilator = new ValidationIndex(repressilatorReport, loadValidation("repressilator"));

describe("ValidationIndex", () => {
  it("looks up the issues of an element and of a type", () => {
    const k1 = validationReport.mainModel?.listOfParameters?.find((p) => p.id === "k1");
    expect(k1).toBeDefined();
    expect(validation.issuesOf(k1!.pk).map((i) => i.rule)).toEqual(
      expect.arrayContaining([10703, 20702]),
    );
    expect(validation.worstSeverity(k1!.pk)).toBe("warning");
    expect(validation.worstSeverity(validationReport.mainModel!.pk)).toBe("error");
    expect(validation.issueCounts.error).toBe(1);
    expect(validation.issueCounts.warning).toBeGreaterThan(3);
    expect(validation.issues).toHaveLength(validation.issueCounts.error + 6);
    expect(validation.skipped).toBeNull();
    const modelId = validationReport.mainModel!.id!;
    expect(validation.worstSeverityOfType("Parameter", modelId)).toBe("warning");
    expect(validation.worstSeverityOfType("Species", modelId)).toBeNull();
    expect(repressilator.issuesOf(repressilatorReport.document.pk)).toEqual([]);
    expect(repressilator.issueCounts.warning).toBeGreaterThan(0);
  });

  it("marks the row which holds an element without a row of its own by the issues of it", () => {
    // the kinetic law of R1 has a warning of its own, it has no table and marks the reaction
    const r1 = validationReport.mainModel!.listOfReactions!.find((r) => r.id === "R1")! as Reaction;
    const law = r1.kineticLaw!.pk;
    const lawIssues = validation.issuesOf(law);
    expect(lawIssues.map((i) => i.rule)).toEqual([99505]);
    expect(validation.issuesOf(r1.pk)).toEqual([]);
    expect(validation.heldIssuesOf(r1.pk)).toEqual(lawIssues);
    expect(validation.worstSeverity(r1.pk)).toBe("warning");
    expect(validation.worstSeverityOfType("Reaction", validationReport.mainModel!.id!)).toBe(
      "warning",
    );
    // the kinetic law keeps its own issues and its own severity, and holds nothing
    expect(validation.worstSeverity(law)).toBe("warning");
    expect(validation.heldIssuesOf(law)).toEqual([]);
    // an element of a table holds nothing of another element of a table
    const k1 = validationReport.mainModel!.listOfParameters!.find((p) => p.id === "k1")!;
    expect(validation.heldIssuesOf(k1.pk)).toEqual([]);
  });

  it("folds the issues of the lists of a model, which have no row, into the model", () => {
    const report = new ReportIndex(loadReport("list_of"));
    const model = report.models[0]!.pk;
    const index = new ValidationIndex(
      report,
      withIssues([
        { pk: model, severity: "warning", rule: 80701 },
        { pk: "list_of/ListOf:metabolites", severity: "error", rule: 20101 },
      ]),
    );
    expect(index.worstSeverity(model)).toBe("error");
    expect(index.heldIssuesOf(model).map((i) => i.rule)).toEqual([20101]);
    expect(index.issuesOf("list_of/ListOf:metabolites").map((i) => i.rule)).toEqual([20101]);
    // the elements of a table of the model are no part of the model's row
    const species = report.byType(report.models[0]!.id!).get("Species")![0]!;
    const held = new ValidationIndex(report, withIssues([{ pk: species.pk, severity: "error" }]));
    expect(held.heldIssuesOf(model)).toEqual([]);
    expect(held.worstSeverity(model)).toBeNull();
  });

  it("lists the issues of a row errors first, a held error before its own warnings", () => {
    const r1 = validationReport.mainModel!.listOfReactions!.find((r) => r.id === "R1")! as Reaction;
    const index = new ValidationIndex(
      validationReport,
      withIssues([
        { pk: r1.pk, severity: "warning", rule: 10501 },
        { pk: r1.pk, severity: "info", rule: 99999 },
        { pk: r1.kineticLaw!.pk, severity: "error", rule: 99505 },
      ]),
    );
    expect(index.rowIssuesOf(r1.pk).map((i) => i.rule)).toEqual([99505, 10501, 99999]);
  });

  it("scopes the worst severity of a type to one model", () => {
    // both models of the fixture state a species, the warning concerns the species of m1 alone
    const definitions = new ReportIndex(loadReport("model_definitions"));
    const main = definitions.mainModel!.id!;
    expect(main).not.toBe("m1");
    expect(definitions.byType(main).get("Species")?.length).toBeGreaterThan(0);
    const index = new ValidationIndex(
      definitions,
      withIssues([{ pk: "m1/Species:A", severity: "warning" }]),
    );
    expect(index.worstSeverityOfType("Species", "m1")).toBe("warning");
    expect(index.worstSeverityOfType("Species", main)).toBeNull();
  });

  it("counts and lists an issue of an element the shown report does not hold", () => {
    // the local server reads the file again for its validation, which may have changed since
    const index = new ValidationIndex(
      validationReport,
      withIssues([
        { pk: "validation/Species:gone", severity: "error", rule: 20601 },
        { pk: validationReport.document.pk, severity: "warning", rule: 10501 },
      ]),
    );
    expect(index.issueCounts).toEqual({ error: 1, warning: 1, info: 0 });
    expect(index.issues.map((i) => i.rule)).toEqual([20601, 10501]);
    expect(index.issuesOf("validation/Species:gone").map((i) => i.rule)).toEqual([20601]);
    expect(index.heldIssuesOf(validationReport.document.pk)).toEqual([]);
    expect(index.worstSeverity(validationReport.document.pk)).toBe("warning");
    expect(index.worstSeverityOfType("Species", validationReport.mainModel!.id!)).toBeNull();
  });

  it("folds the issues of elements nested several levels deep into the row which holds them", () => {
    const events = new ReportIndex(loadReport("constraint_event"));
    const fbc = new ReportIndex(loadReport("fbc_constraints_v3"));
    // a local parameter of the kinetic law of a reaction, the trigger and an assignment of an event
    const parameter = "constraint_event/LocalParameter:R1.kineticLaw.Vmax";
    const trigger = "constraint_event/Trigger:E1_trigger";
    const assignment = "constraint_event/EventAssignment:E1_switch";
    const reaction = "constraint_event/Reaction:R1";
    const event = "constraint_event/Event:E1";
    const nested = new ValidationIndex(
      events,
      withIssues([
        { pk: parameter, severity: "warning", rule: 21121 },
        { pk: trigger, severity: "error", rule: 21202 },
        { pk: assignment, severity: "warning", rule: 21211 },
      ]),
    );
    expect(events.holderOf(parameter)).toBe(reaction);
    expect(nested.heldIssuesOf(reaction).map((i) => i.pk)).toEqual([parameter]);
    expect(nested.worstSeverity(reaction)).toBe("warning");
    expect(nested.heldIssuesOf(event).map((i) => i.pk)).toEqual([trigger, assignment]);
    expect(nested.rowIssuesOf(event).map((i) => i.rule)).toEqual([21202, 21211]);
    expect(nested.worstSeverity(event)).toBe("error");
    const model = events.mainModel!.id!;
    expect(nested.worstSeverityOfType("Event", model)).toBe("error");
    expect(nested.worstSeverityOfType("Reaction", model)).toBe("warning");
    // the nested elements hold nothing themselves
    expect(nested.heldIssuesOf(trigger)).toEqual([]);

    // a gene product reference of an and below an or of the association of a reaction, and the
    // and itself
    const ref = "fbc_constraints_v3/GeneProductRef:gpa_v1.association.0.1";
    const and = "fbc_constraints_v3/And:gpa_v1.association.0";
    const v1 = "fbc_constraints_v3/Reaction:v1";
    const association = new ValidationIndex(
      fbc,
      withIssues([
        { pk: ref, severity: "warning", rule: 10501 },
        { pk: and, severity: "error", rule: 21201 },
      ]),
    );
    expect(fbc.holderOf(ref)).toBe(v1);
    expect(fbc.holderOf(and)).toBe(v1);
    expect(association.rowIssuesOf(v1).map((i) => i.pk)).toEqual([and, ref]);
    expect(association.worstSeverity(v1)).toBe("error");
    expect(association.worstSeverityOfType("Reaction", fbc.mainModel!.id!)).toBe("error");
  });

  it("marks no type by an issue of an element of another entry", () => {
    // the pk of an element of another report: the answer of a local server reads the files again
    const events = new ReportIndex(loadReport("constraint_event"));
    const foreign = repressilatorReport.mainModel!.listOfSpecies![0]!.pk;
    expect(events.get(foreign)).toBeUndefined();
    const index = new ValidationIndex(
      events,
      withIssues([{ pk: foreign, severity: "error", rule: 20601 }]),
    );
    expect(index.issueCounts.error).toBe(1);
    expect(index.worstSeverityOfType("Species", events.mainModel!.id!)).toBeNull();
    expect(index.worstSeverityOfType("Species", repressilatorReport.mainModel!.id!)).toBeNull();
    for (const species of events.byType(events.mainModel!.id!).get("Species") ?? []) {
      expect(index.worstSeverity(species.pk)).toBeNull();
    }
  });

  it("keeps why the document was not validated", () => {
    const fanOut = new ReportIndex(loadReport("fan_out"));
    const index = new ValidationIndex(fanOut, loadValidation("fan_out"));
    expect(index.skipped).toBe("expandedSize");
    expect(index.issues).toEqual([]);
    expect(index.issueCounts).toEqual({ error: 0, warning: 0, info: 0 });
  });
});
