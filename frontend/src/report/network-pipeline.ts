import { computeLayout } from "@graphvis/viewer/layout";
import type { Scene } from "@graphvis/viewer";
import type { Report } from "@/api/types";
import { ReportIndex } from "@/report/index";
import {
  buildNetwork,
  networkScene,
  networkLayout,
  type NetworkKind,
  type NetworkProjection,
} from "@/report/network";
import { nodeColors, color, relationStyle } from "@/report/network-style";

export type Palette = Pick<
  Scene,
  "colors" | "strokeColors" | "linkColors" | "background" | "foreground"
>;
export interface NetworkRequest {
  entry: string | null;
  model: string | null;
  kind: NetworkKind;
  biological: boolean;
  spacing: number;
}
export interface PreparedNetwork {
  projection: Omit<NetworkProjection, "nodes"> & {
    nodes: Omit<NetworkProjection["nodes"][number], "index" | "element">[];
  };
  scene: Scene;
  dark: Palette;
}

const OMIT = new Set([
  "xml",
  "annotationXml",
  "notes",
  "cvterms",
  "history",
  "math",
  "odeSystem",
  "equation",
]);
const REFERENCES = new Set(["pk", "source", "target", "model"]);
export interface NetworkInput {
  keys: string[];
  reports: Record<string, unknown>;
}
/** Intern repeated primary keys before cloning. XML and resolver metadata stay on the UI thread. */
export function networkInput(index: ReportIndex): NetworkInput {
  const entries = index.networkEntries();
  const keys = [
    ...new Set(
      entries.flatMap(([location]) => {
        const entry = index.entry(location)!;
        return [...entry.elements.keys(), ...entry.nodes.keys()];
      }),
    ),
  ];
  const identifiers = new Map(keys.map((key, i) => [key, i]));
  const compact = (value: unknown): unknown => {
    if (Array.isArray(value)) return value.map(compact);
    if (!value || typeof value !== "object") return value;
    const result: Record<string, unknown> = {};
    for (const key in value) {
      if (OMIT.has(key)) continue;
      const child = (value as Record<string, unknown>)[key];
      if (child === null || child === undefined || (Array.isArray(child) && !child.length))
        continue;
      if (key === "nodes") result[key] = Object.values(child).map(compact);
      else if (REFERENCES.has(key) && typeof child === "string")
        result[key] = identifiers.get(child) ?? child;
      else result[key] = compact(child);
    }
    return result;
  };
  return {
    keys,
    reports: Object.fromEntries(
      entries.map(([location, report]) => [location ?? "", { report: compact(report) }]),
    ),
  };
}

/** UTF-8 transfer avoids cloning hundreds of thousands of nested objects on the UI thread. */
export function encodeNetworkInput(input: NetworkInput): Uint8Array {
  return new TextEncoder().encode(JSON.stringify(input));
}

export function decodeNetworkInput(bytes: Uint8Array): NetworkInput {
  return JSON.parse(new TextDecoder().decode(bytes)) as NetworkInput;
}

function expandInput(input: NetworkInput): Record<string, { report: Report }> {
  const expand = (value: unknown): unknown => {
    if (Array.isArray(value)) return value.map(expand);
    if (!value || typeof value !== "object") return value;
    const result: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(value)) {
      if (key === "nodes")
        result[key] = Object.fromEntries(
          (child as unknown[]).map((value) => {
            const node = expand(value) as { pk: string };
            return [node.pk, node];
          }),
        );
      else
        result[key] =
          REFERENCES.has(key) && typeof child === "number" ? input.keys[child] : expand(child);
    }
    return result;
  };
  return expand(input.reports) as Record<string, { report: Report }>;
}

/** Retain one topology and a bounded position cache in the worker, never DOM or resolver objects. */
export class NetworkPipeline {
  private indexes: Map<string, ReportIndex>;
  private cached: {
    key: string;
    projection: NetworkProjection;
    scene: Scene;
    dark: Palette;
  } | null = null;
  private positions = new Map<string, Float32Array>();
  constructor(input: NetworkInput) {
    const reports = expandInput(input);
    this.indexes = reports[""]
      ? new Map([["", new ReportIndex(reports[""].report)]])
      : ReportIndex.forEntries(reports);
  }

  prepare(request: NetworkRequest): PreparedNetwork {
    const index = this.indexes.get(request.entry ?? "");
    if (!index) throw new Error("The network report is no longer available.");
    const key = JSON.stringify([
      request.entry,
      request.kind === "all" ? null : request.model,
      request.kind,
    ]);
    if (this.cached?.key !== key) {
      const model = index.models.find((model) => model.pk === request.model) ?? null;
      const projection = buildNetwork(index, model, request.kind, "light");
      const scene = networkScene(projection, "light");
      const colors = new Float32Array(scene.colors.length),
        strokeColors = new Float32Array(scene.strokeColors.length);
      projection.nodes.forEach((node, i) => {
        const palette = nodeColors(
          node.sbmlType,
          node.element?.sbmlType === "Reaction" && node.element.reversible === true,
          "dark",
        );
        colors.set(palette.color, i * 4);
        strokeColors.set(palette.strokeColor, i * 4);
      });
      const linkColors = new Float32Array(scene.linkColors.length);
      projection.edges.forEach((edge, i) => {
        const participation = [
          "reactant",
          "product",
          "modifier",
          "activator",
          "inhibitor",
          "input",
          "output",
        ].includes(edge.kind);
        const ink =
          request.kind !== "all" && participation && edge.entityId === undefined
            ? edge.kind === "inhibitor"
              ? color("#cc2222")
              : edge.kind === "activator"
                ? color("#006600")
                : edge.kind === "modifier"
                  ? color("#3333ff")
                  : color("#dbe3eb")
            : relationStyle(edge.kind, "dark").color;
        linkColors.set(ink, i * 4);
      });
      this.cached = {
        key,
        projection,
        scene,
        dark: { colors, strokeColors, linkColors, background: "#17212b", foreground: "#eeeeee" },
      };
    }
    const { projection, scene, dark } = this.cached;
    const layoutKey = `${key}:${request.biological}:${request.spacing}`;
    let positions = this.positions.get(layoutKey);
    if (!positions) {
      positions = computeLayout(
        scene.ids.length,
        scene.links,
        networkLayout(projection, request.biological, request.spacing),
      );
      // Keep at most 12 layouts and 32 MiB of coordinates, including large models.
      const bytes = () =>
        [...this.positions.values()].reduce((sum, value) => sum + value.byteLength, 0);
      while (
        this.positions.size &&
        (this.positions.size >= 12 || bytes() + positions.byteLength > 32 * 1024 * 1024)
      )
        this.positions.delete(this.positions.keys().next().value!);
      if (positions.byteLength <= 32 * 1024 * 1024) this.positions.set(layoutKey, positions);
    }
    return {
      projection: {
        ...projection,
        nodes: projection.nodes.map((node) => {
          const wire: Partial<typeof node> = { ...node };
          delete wire.index;
          delete wire.element;
          return wire as PreparedNetwork["projection"]["nodes"][number];
        }),
      },
      scene: { ...scene, positions },
      dark,
    };
  }
}

/** Copy cache-owned buffers once, then transfer ownership to the UI thread. */
export function transferableNetwork(prepared: PreparedNetwork): {
  result: PreparedNetwork;
  transfer: ArrayBuffer[];
} {
  const result = structuredClone(prepared);
  const buffers = new Set<ArrayBuffer>();
  for (const value of [...Object.values(result.scene), ...Object.values(result.dark)])
    if (value instanceof Float32Array) buffers.add(value.buffer as ArrayBuffer);
  return { result, transfer: [...buffers] };
}
