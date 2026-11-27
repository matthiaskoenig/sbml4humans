import { describe, expect, it } from "vitest";
import { ReportIndex } from "@/report/index";
import { buildNetwork, networkScene } from "@/report/network";
import {
  NetworkPipeline,
  networkInput,
  encodeNetworkInput,
  decodeNetworkInput,
  transferableNetwork,
} from "@/report/network-pipeline";
import { loadFixture, loadReport } from "./fixtures";

describe("worker network preparation", () => {
  for (const fixture of [
    "repressilator",
    "model_definitions",
    "comp_deletion",
    "fbc_example",
    "fbc_bounds_v1",
    "fbc_constraints_v3",
    "distrib_uncertainties",
    "distrib_spans",
    "constraint_event",
    "qual_example",
    "list_of",
    "fan_out",
  ] as const)
    for (const kind of ["base", "kinetic", "all"] as const)
      it(`preserves ${fixture} ${kind} objects, links and palettes`, () => {
        const index = new ReportIndex(loadReport(fixture));
        const source = networkInput(index);
        expect(JSON.stringify(source)).not.toContain('"xml":');
        const encoded = encodeNetworkInput(source);
        const received = structuredClone(encoded, { transfer: [encoded.buffer as ArrayBuffer] });
        const pipeline = new NetworkPipeline(decodeNetworkInput(received));
        const request = {
          entry: null,
          model: index.mainModel?.pk ?? null,
          kind,
          biological: false,
          spacing: 1,
        };
        const result = pipeline.prepare(request);
        const expected = networkScene(
          buildNetwork(index, index.mainModel ?? null, kind, "dark"),
          "dark",
        );
        expect(result.scene.ids).toEqual(expected.ids);
        expect(result.scene.links).toEqual(expected.links);
        expect(result.dark.colors).toEqual(expected.colors);
        expect(result.dark.strokeColors).toEqual(expected.strokeColors);
        expect(result.dark.linkColors).toEqual(expected.linkColors);
        expect(
          result.projection.nodes.every((node) => !("index" in node) && !("element" in node)),
        ).toBe(true);
        const again = pipeline.prepare(request);
        expect(again.scene.positions).toBe(result.scene.positions);
        expect(again.scene.links).toBe(result.scene.links);
        const outgoing = transferableNetwork(result);
        structuredClone(outgoing.result, { transfer: outgoing.transfer });
        expect(result.scene.positions.byteLength).toBe(result.scene.ids.length * 8);
      });

  it("preserves archive boundaries with original entry identities", () => {
    const fixture = loadFixture("comp_models");
    const indexes = ReportIndex.forEntries(fixture.reports);
    for (const [entry, index] of indexes) {
      const result = new NetworkPipeline(networkInput(index)).prepare({
        entry,
        model: null,
        kind: "all",
        biological: false,
        spacing: 1,
      });
      const expected = buildNetwork(index, null, "all", "light");
      expect(result.projection.nodes.map((node) => [node.id, node.pk, node.entry])).toEqual(
        expected.nodes.map((node) => [node.id, node.pk, node.entry]),
      );
      expect(result.projection.edges).toEqual(expected.edges);
    }
  });
});
