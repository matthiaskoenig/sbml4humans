import { describe, expect, it } from "vitest";

import { ReportIndex } from "@/report/index";
import { buildNetwork, networkScene } from "@/report/network";

import { loadFixture, loadReport } from "./fixtures";

describe("SBML network projections", () => {
  it("includes every reported object, all model definitions, and explicit containment", () => {
    const index = new ReportIndex(loadReport("model_definitions"));
    const graph = buildNetwork(index, index.mainModel!, "all", "light");
    expect(graph.nodes.some((n) => n.pk === index.document.pk)).toBe(true);
    for (const pk of index.elements.keys()) expect(graph.nodes.some((n) => n.pk === pk)).toBe(true);
    for (const model of index.models) expect(graph.nodes.some((n) => n.pk === model.pk)).toBe(true);
    expect(
      graph.edges.some(
        (e) => e.source === index.document.pk && ["contains", "model"].includes(e.kind),
      ),
    ).toBe(true);
    expect(graph.nodes.length).toBeGreaterThan(
      buildNetwork(index, index.mainModel!, "base", "light").nodes.length,
    );
    const empty = structuredClone(index.report);
    empty.models = [];
    empty.linkGraph = { nodes: {}, edges: [] };
    const document = new ReportIndex(empty);
    expect(buildNetwork(document, null, "all", "light").nodes.map((n) => n.pk)).toContain(
      document.document.pk,
    );
  });

  it("retains cross-entry boundaries and qualifies their identities", () => {
    const indexes = ReportIndex.forEntries(loadFixture("comp_models").reports);
    const index = [...indexes.values()][0]!;
    const graph = buildNetwork(index, index.mainModel!, "all", "light");
    const external = graph.nodes.filter((n) => n.external);
    expect(external.length).toBeGreaterThan(0);
    for (const node of external) {
      expect(node.id).not.toBe(node.pk);
      expect(node.index.location).toBe(node.entry);
      expect(node.index.has(node.pk)).toBe(true);
    }
    expect(new Set(graph.nodes.map((n) => n.id)).size).toBe(graph.nodes.length);
  });
  it("rejects ambiguous identifier fallback in reports without reference links", () => {
    const report = structuredClone(loadReport("repressilator"));
    report.linkGraph = { nodes: {}, edges: [] };
    const model = report.models![0]!;
    const first = model.listOfSpecies![0]!;
    model.listOfSpecies![1]!.id = first.id;
    const reference = model.listOfReactions!.flatMap((r) => r.listOfProducts ?? [])[0]!;
    reference.species = first.id!;
    const graph = buildNetwork(new ReportIndex(report), model, "base", "light");
    expect(graph.unresolved).toContain(reference.pk);
    expect(graph.edges.some((e) => e.id === reference.pk)).toBe(false);
  });
  it("keeps canonical species/reaction keys and participant direction from a real report", () => {
    const index = new ReportIndex(loadReport("repressilator"));
    const model = index.mainModel!;
    const original = JSON.stringify(model);
    const graph = buildNetwork(index, model, "base", "light");
    expect(graph.nodes.filter((n) => n.sbmlType === "Species")).toHaveLength(6);
    expect(graph.nodes.filter((n) => n.sbmlType === "Reaction")).toHaveLength(12);
    expect(graph.edges).toHaveLength(18);
    for (const reaction of model.listOfReactions ?? []) {
      for (const reference of reaction.listOfProducts ?? []) {
        const edge = graph.edges.find((e) => e.id === reference.pk)!;
        expect(edge.source).toBe(reaction.pk);
        expect(index.get(edge.target)?.id).toBe(reference.species);
        expect(edge.stoichiometry).toBe(reference.stoichiometry);
      }
      for (const reference of reaction.listOfReactants ?? []) {
        expect(graph.edges.find((e) => e.id === reference.pk)?.target).toBe(reaction.pk);
      }
    }
    expect(graph.nodes.every((n) => index.has(n.pk))).toBe(true);
    expect(graph.unresolved).toEqual([]);
    expect(JSON.stringify(model)).toBe(original);
  });

  it("preserves participant keys and coefficients in an FBC model", () => {
    const index = new ReportIndex(loadReport("fbc_example"));
    const model = index.mainModel!;
    const graph = buildNetwork(index, model, "base", "light");
    expect(graph.nodes).toHaveLength(12);
    expect(graph.edges).toHaveLength(17);
    for (const reaction of model.listOfReactions ?? [])
      for (const reference of reaction.listOfReactants ?? []) {
        expect(graph.edges.find((e) => e.id === reference.pk)?.stoichiometry).toBe(
          reference.stoichiometry,
        );
      }
  });

  it("uses resolved mathematical dependencies and includes local parameters in kinetic view", () => {
    const index = new ReportIndex(loadReport("constraint_event"));
    const model = index.mainModel!;
    const graph = buildNetwork(index, model, "kinetic", "light");
    for (const reaction of model.listOfReactions ?? [])
      if (reaction.kineticLaw) {
        const law = reaction.kineticLaw;
        expect(graph.nodes.some((n) => n.pk === law.pk)).toBe(true);
        for (const local of law.listOfLocalParameters ?? [])
          expect(graph.nodes.some((n) => n.pk === local.pk)).toBe(true);
        for (const edge of index.references(law.pk).filter((e) => e.kind === "math")) {
          expect(
            graph.edges.some(
              (e) => e.source === edge.target && e.target === law.pk && e.kind === "math",
            ),
          ).toBe(true);
        }
      }
    expect(graph.nodes.some((n) => n.sbmlType === "Event")).toBe(true);
  });

  it("draws qualitative models without requiring core species or reactions", () => {
    const index = new ReportIndex(loadReport("qual_example"));
    const graph = buildNetwork(index, index.mainModel!, "base", "light");
    expect(graph.nodes.some((n) => n.sbmlType === "QualitativeSpecies")).toBe(true);
    expect(graph.nodes.some((n) => n.sbmlType === "Transition")).toBe(true);
    expect(graph.edges.length).toBeGreaterThan(0);
    expect(graph.unresolved).toEqual([]);
  });

  it("keeps archive entries distinct even when their model keys coincide", () => {
    const indexes = ReportIndex.forEntries(loadFixture("comp_models").reports);
    const projections = [...indexes.values()].map((index) =>
      buildNetwork(index, index.mainModel!, "base", "light"),
    );
    expect(new Set(projections.map((p) => p.scope)).size).toBe(projections.length);
    for (const [location, index] of indexes) {
      const graph = buildNetwork(index, index.mainModel!, "all", "light");
      expect(graph.nodes.every((n) => n.index.has(n.pk))).toBe(true);
      expect(JSON.parse(graph.scope)[0]).toBe(location);
    }
  });

  it("includes reference objects only in all objects view and supports models without ids", () => {
    const report = structuredClone(loadReport("repressilator"));
    const model = report.models![0]!;
    model.id = null;
    const index = new ReportIndex(report);
    const base = buildNetwork(index, model, "base", "light");
    const all = buildNetwork(index, model, "all", "dark");
    expect(base.nodes).toHaveLength(18);
    const reference = model.listOfReactions!.flatMap((r) => r.listOfProducts ?? [])[0]!;
    expect(base.nodes.some((n) => n.pk === reference.pk)).toBe(false);
    expect(all.nodes.some((n) => n.pk === reference.pk)).toBe(true);
    expect(networkScene(all, "dark").background).toBe("#17212b");
  });

  it("reports unresolved references without guessing their species", () => {
    const report = structuredClone(loadReport("repressilator"));
    const model = report.models![0]!;
    const reference = model.listOfReactions!.flatMap((r) => r.listOfProducts ?? [])[0]!;
    reference.species = "unknown_species";
    const graph = buildNetwork(new ReportIndex(report), model, "base", "light");
    expect(graph.unresolved).toContain(reference.pk);
    expect(graph.edges.some((e) => e.id === reference.pk)).toBe(false);
  });
});
