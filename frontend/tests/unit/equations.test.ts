import { describe, expect, it } from "vitest";

import type { OdeEquation } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { renderLatex } from "@/report/latex";

import { loadFixture, loadReport, type FixtureName } from "./fixtures";

const repressilator = new ReportIndex(loadReport("repressilator"));

describe("the equations of a report", () => {
  it("has the ODE system of the model", () => {
    const system = repressilator.odeSystem;
    expect(system).not.toBeNull();
    expect(system!.odes).toHaveLength(6);
    expect(system!.reactions).toHaveLength(12);
    expect(repressilator.odeError).toBeNull();
  });

  it("finds the equations of an element by its pk", () => {
    const px = repressilator.equationsOf("BIOMD0000000012/Species:PX");
    expect(px.map((e) => e.section)).toEqual(["odes"]);
    expect(px[0]!.equation.origin).toBe("reactions");
    const reaction = repressilator.equationsOf("BIOMD0000000012/Reaction:Reaction1");
    expect(reaction.map((e) => e.section)).toEqual(["reactions"]);
    expect(repressilator.equationsOf("BIOMD0000000012/Compartment:cell")).toEqual([]);
    expect(repressilator.equationsOf("unknown")).toEqual([]);
  });

  it("renders every equation of every fixture with KaTeX, its symbols as links", () => {
    const names: FixtureName[] = [
      "repressilator",
      "cell_cycle",
      "icg_body",
      "fbc_example",
      "comp_models",
      "constraint_event",
      "distrib_uncertainties",
      "qual_example",
    ];
    let rendered = 0;
    for (const name of names) {
      for (const entry of Object.values(loadFixture(name).reports)) {
        const system = entry.report.odeSystem;
        if (!system) continue;
        const equations: OdeEquation[] = [
          ...(system.odes ?? []),
          ...(system.reactions ?? []),
          ...(system.assignments ?? []),
          ...(system.functions ?? []),
          ...(system.initial ?? []),
          ...(system.events ?? []).flatMap((event) => event.assignments ?? []),
        ];
        for (const equation of equations) {
          for (const latex of [equation.lhs, ...equation.lines]) {
            const html = renderLatex(latex, { links: true });
            expect(html, `${name}: ${latex}`).not.toBeNull();
            expect(html, `${name}: ${latex}`).not.toContain("katex-error");
            expect(html, `${name}: ${latex}`).not.toContain("color:#cc0000");
            rendered += 1;
          }
        }
      }
    }
    expect(rendered).toBeGreaterThan(100);
  });
});
