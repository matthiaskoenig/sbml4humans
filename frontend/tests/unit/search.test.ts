import { describe, expect, it } from "vitest";

import type { Species } from "@/api/types";
import { ReportIndex } from "@/report/index";
import { matches, normalizeQuery } from "@/report/search";

import { loadReport } from "./fixtures";

const index = new ReportIndex(loadReport("repressilator"));
const model = index.mainModel!;

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

  it("does not match a species by the compartment id", () => {
    const species = model.listOfSpecies![0] as Species;
    if (!species.id!.includes(species.compartment)) {
      expect(matches(species, species.compartment)).toBe(false);
    }
  });
});
