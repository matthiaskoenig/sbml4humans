import { describe, expect, it } from "vitest";

import type { AssignmentRule, Species } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { matches, normalizeQuery } from "@/report/search";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const model = index.mainModel!;
const spans = new ReportIndex(loadReport("distrib_spans")).mainModel!;

describe("search", () => {
  it("normalizes the query", () => {
    expect(normalizeQuery("  LacI ")).toBe("laci");
  });

  it("matches everything for the empty query", () => {
    expect(matches(model.listOfSpecies![0]!, "")).toBe(true);
    expect(matches(model.listOfSpecies![0]!, "   ")).toBe(true);
  });

  it("matches id, name and metaId case insensitively", () => {
    const species = model.listOfSpecies!.find((s) => s.name)!;
    expect(matches(species, species.id!.toUpperCase())).toBe(true);
    expect(matches(species, species.name!.slice(0, 4).toLowerCase())).toBe(true);
    if (species.metaId) expect(matches(species, species.metaId)).toBe(true);
    expect(matches(species, "definitely-not-there")).toBe(false);
  });

  it("matches the sbo term", () => {
    const withSbo = [...index.elements.values()].find((e) => e.sbo);
    if (withSbo) expect(matches(withSbo, withSbo.sbo!)).toBe(true);
  });

  it("matches the formula of the math and the equation of a reaction", () => {
    const reaction = model.listOfReactions!.find((r) => r.kineticLaw?.math)!;
    const symbol = reaction.kineticLaw!.math!.formula.match(/[A-Za-z_]\w*/)![0];
    expect(matches(reaction, symbol)).toBe(true);
    const reactant = reaction.equation.split(/\s|->|=>|<=>/).find((t) => t && !/^\d+$/.test(t))!;
    expect(matches(reaction, reactant)).toBe(true);
  });

  it("matches the text of the notes without the html tags", () => {
    const withNotes = [...index.elements.values()].find((e) => e.notes && /<p>/.test(e.notes))!;
    const text = withNotes
      .notes!.replace(/<[^>]+>/g, " ")
      .trim()
      .split(/\s+/)[0]!;
    expect(matches(withNotes, text)).toBe(true);
    expect(matches(withNotes, "<p>")).toBe(false);
  });

  it("matches a rule by the variable it sets", () => {
    // the rules of a Level 2 model have no id, and a reader looks for the element they set
    const rule = model.listOfRules!.find((r) => "variable" in r)!;
    expect(rule.id).toBeNull();
    expect(matches(rule, (rule as AssignmentRule).variable)).toBe(true);
  });

  it("matches an element by the uncertainties it carries and their measures", () => {
    // an uncertainty is no row of a table, it is shown in the inspector of its element: the
    // element is found by the name, the notes and the measures of its uncertainties
    const parameter = (id: string) => spans.listOfParameters!.find((p) => p.id === id)!;
    const substrate = spans.listOfSpecies!.find((s) => s.id === "S")!;
    expect(matches(parameter("Km"), "Baker")).toBe(true);
    expect(matches(parameter("Km"), "lysate")).toBe(true);
    expect(matches(parameter("Km"), "Km_purified_mean")).toBe(true);
    expect(matches(parameter("Km"), "confidenceInterval")).toBe(true);
    expect(matches(substrate, "titration")).toBe(true);
    expect(matches(substrate, "five titrations")).toBe(true);
    // the parameters of a distribution, however deep they nest
    expect(matches(parameter("Vmax"), "Beta")).toBe(true);
    expect(matches(parameter("Vmax"), "Vmax_alpha")).toBe(true);
    expect(matches(parameter("Km_lower"), "Baker")).toBe(false);
  });

  it("matches a rule by the name of the element it sets", () => {
    // the promise of the documentation: a rule without an id is found by the name of what it sets
    const rule = model.listOfRules!.find((r) => "variable" in r && r.variable === "t_ave")!;
    const parameter = model.listOfParameters!.find((p) => p.id === "t_ave")!;
    expect(parameter.name).toBeTruthy();
    expect(matches(rule, parameter.name!, index)).toBe(true);
    expect(matches(rule, parameter.name!)).toBe(false);
  });

  it("matches an element by the elements it nests and a gene product by its label", () => {
    const qual = new ReportIndex(loadReport("qual_example"));
    const transition = qual.mainModel!.listOfTransitions!.find((t) => t.id === "tr_G")!;
    expect(matches(transition, "threshold of the signal", qual)).toBe(true);
    expect(matches(transition, "theta_G_S", qual)).toBe(true);

    const deletion = new ReportIndex(loadReport("comp_deletion"));
    const submodel = deletion.mainModel!.listOfSubmodels!.find((s) => s.id === "cell1")!;
    expect(matches(submodel, "del_k", deletion)).toBe(true);
    expect(matches(submodel, "deletion of the sink", deletion)).toBe(true);
    // an element is found by the port its replacement names in a submodel
    const medium = deletion.mainModel!.listOfCompartments!.find((c) => c.id === "medium")!;
    expect(matches(medium, "cell_port", deletion)).toBe(true);

    const fbc = new ReportIndex(loadReport("fbc_constraints_v3"));
    const gene = fbc.mainModel!.listOfGeneProducts!.find((g) => g.id === "g_ptsG")!;
    expect(matches(gene, "b1101", fbc)).toBe(true);
  });

  it("does not match a species by the compartment id", () => {
    const species = model.listOfSpecies![0] as Species;
    if (!species.id!.includes(species.compartment)) {
      expect(matches(species, species.compartment)).toBe(false);
    }
  });
});
