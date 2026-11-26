import { packScene, type Scene, type VisualEdge, type VisualNode } from "@graphvis/viewer";

import type { EdgeKind, Model, SBase } from "@/api/types";
import type { ReportIndex } from "@/report/index";
import type { NetworkKind } from "@/report/query";
import { completeNetwork } from "@/report/network-complete";
import { visualNode, color, relationStyle } from "@/report/network-style";

export type { NetworkKind } from "@/report/query";
export type NetworkTheme = "light" | "dark";

export interface NetworkNode extends VisualNode {
  pk: string;
  sbmlType: string;
  name: string;
  entry: string | null;
  model: string | null;
  element?: SBase;
  index: ReportIndex;
  inspectable: boolean;
  group: string;
  external: boolean;
}
export interface NetworkEdge extends VisualEdge {
  kind: string;
  stoichiometry?: number | string | null;
  external?: boolean;
}
export interface NetworkProjection {
  scope: string;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  unresolved: string[];
}

const ACTIVATORS = new Set([13, 21, 459, 460, 461, 462, 533, 534, 535]);
const INHIBITORS = new Set([20, 206, 207, 536, 537, 597]);
const BASE_TYPES = new Set(["Species", "Reaction", "QualitativeSpecies", "Transition"]);
const KINETIC_TYPES = new Set([
  ...BASE_TYPES,
  "KineticLaw",
  "Parameter",
  "Compartment",
  "LocalParameter",
  "FunctionDefinition",
  "AssignmentRule",
  "RateRule",
  "AlgebraicRule",
  "InitialAssignment",
  "Constraint",
  "Event",
  "Trigger",
  "Priority",
  "Delay",
  "EventAssignment",
  "FunctionTerm",
  "DefaultTerm",
]);

function uniqueIds(elements: { id?: string | null; pk: string }[]): Map<string, string | null> {
  const ids = new Map<string, string | null>();
  for (const element of elements)
    if (element.id) {
      ids.set(element.id, ids.has(element.id) ? null : element.pk);
    }
  return ids;
}

/** Collect the objects physically nested in this model, including models without an SId. */
function objectsOf(model: Model): Map<string, SBase> {
  const objects = new Map<string, SBase>();
  const walk = (value: unknown): void => {
    if (!value || typeof value !== "object") return;
    if (Array.isArray(value)) {
      value.forEach(walk);
      return;
    }
    if ("pk" in value && typeof value.pk === "string") objects.set(value.pk, value as SBase);
    for (const child of Object.values(value)) if (typeof child === "object") walk(child);
  };
  walk(model);
  return objects;
}

/** Derive graphs from the report. This adapter never reparses XML or changes SBML identity. */
export function buildNetwork(
  index: ReportIndex,
  model: Model | null,
  kind: NetworkKind,
  theme: NetworkTheme,
): NetworkProjection {
  if (kind === "all") return completeNetwork(index, theme);
  if (!model)
    return {
      scope: JSON.stringify([index.location, null, kind]),
      nodes: [],
      edges: [],
      unresolved: [],
    };
  const objects = objectsOf(model);
  const nodes = new Map<string, NetworkNode>();
  const edges: NetworkEdge[] = [],
    unresolved: string[] = [];
  for (const element of objects.values()) {
    const type = element.sbmlType ?? "";
    if ((kind === "base" ? BASE_TYPES : KINETIC_TYPES).has(type)) {
      nodes.set(element.pk, visualNode(index, element, theme));
    }
  }
  if (kind === "kinetic") {
    for (const source of nodes.keys())
      for (const edge of index.references(source)) {
        const referenced = objects.get(edge.target);
        if (edge.kind === "math" && referenced && !nodes.has(edge.target)) {
          nodes.set(edge.target, visualNode(index, referenced, theme));
        }
      }
  }
  const ink = color(theme === "dark" ? "#dbe3eb" : "#333333");
  {
    const species = uniqueIds(model.listOfSpecies ?? []);
    const qualitative = uniqueIds(model.listOfQualitativeSpecies ?? []);
    const resolve = (
      pk: string,
      role: EdgeKind,
      id: string,
      fallback: Map<string, string | null>,
    ): string | null => {
      const target = index.resolve(pk, role, id) ?? fallback.get(id);
      if (target && nodes.has(target)) return target;
      unresolved.push(pk);
      return null;
    };
    for (const reaction of model.listOfReactions ?? []) {
      for (const [role, references] of [
        ["reactant", reaction.listOfReactants ?? []],
        ["product", reaction.listOfProducts ?? []],
        ["modifier", reaction.listOfModifiers ?? []],
      ] as const)
        for (const reference of references) {
          const target = resolve(reference.pk, role, reference.species, species);
          if (!target) continue;
          const sbo = Number(reference.sbo?.replace(/^SBO:/, ""));
          const modifier = role === "modifier";
          const relation = modifier
            ? INHIBITORS.has(sbo)
              ? "inhibitor"
              : ACTIVATORS.has(sbo)
                ? "activator"
                : "modifier"
            : role;
          edges.push({
            id: reference.pk,
            source: role === "product" ? reaction.pk : target,
            target: role === "product" ? target : reaction.pk,
            kind: relation,
            color:
              relation === "inhibitor"
                ? color("#cc2222")
                : relation === "activator"
                  ? color("#006600")
                  : modifier
                    ? color("#3333ff")
                    : ink,
            width: 1.4,
            style: modifier ? 1 : 0,
            arrow: false,
            startMarker: role === "reactant" && reaction.reversible ? "triangle" : "none",
            endMarker:
              role === "product"
                ? "triangle"
                : relation === "inhibitor"
                  ? "bar"
                  : relation === "activator"
                    ? "diamond"
                    : modifier
                      ? "circle"
                      : "none",
            label: relation,
            stoichiometry: "stoichiometry" in reference ? reference.stoichiometry : undefined,
          });
        }
    }
    for (const transition of model.listOfTransitions ?? []) {
      for (const [role, references] of [
        ["input", transition.listOfInputs ?? []],
        ["output", transition.listOfOutputs ?? []],
      ] as const) {
        for (const reference of references) {
          const target = resolve(reference.pk, role, reference.qualitativeSpecies, qualitative);
          if (target)
            edges.push({
              id: reference.pk,
              source: role === "output" ? transition.pk : target,
              target: role === "output" ? target : transition.pk,
              kind: role,
              color: ink,
              arrow: true,
            });
        }
      }
    }
  }
  if (kind !== "base") {
    for (const source of nodes.keys())
      for (const edge of index.references(source)) {
        if (!nodes.has(edge.target)) continue;
        if (kind === "kinetic" && ["reactant", "product", "modifier"].includes(edge.kind)) continue;
        const reverse = kind === "kinetic" && edge.kind === "math";
        edges.push({
          id: `${source}:${edge.kind}:${edge.target}:${edges.length}`,
          entityId: source,
          source: reverse ? edge.target : source,
          target: reverse ? source : edge.target,
          kind: edge.kind,
          ...relationStyle(edge.kind, theme),
          label: edge.kind,
        });
      }
  }
  return {
    scope: JSON.stringify([index.location, model.pk, kind]),
    nodes: [...nodes.values()],
    edges,
    unresolved,
  };
}

export function networkScene(projection: NetworkProjection, theme: NetworkTheme): Scene {
  return packScene(projection.nodes, projection.edges, {
    key: projection.scope,
    background: theme === "dark" ? "#17212b" : "#ffffff",
    foreground: theme === "dark" ? "#eeeeee" : "#222222",
  });
}

/** Biology supplies layout hints; the generic worker knows only numeric arrays. */
export function networkLayout(projection: NetworkProjection, biological = true, spacing = 1) {
  const groupIds = new Map<string, number>();
  const groups = Uint32Array.from(projection.nodes, (node) => {
    if (!groupIds.has(node.group)) groupIds.set(node.group, groupIds.size);
    return groupIds.get(node.group)!;
  });
  const radii = Float32Array.from(projection.nodes, (node) => (node.size ?? 20) / 2 + 7);
  if (!biological) return { radii, spacing };
  const distances = Float32Array.from(projection.edges, (edge) =>
    edge.kind === "contains"
      ? 95
      : ["modifier", "inhibitor", "activator", "math"].includes(edge.kind)
        ? 150
        : edge.kind === "units"
          ? 95
          : 105,
  );
  const strengths = Float32Array.from(projection.edges, (edge) =>
    edge.kind === "contains"
      ? 0.04
      : edge.kind === "math" || edge.kind === "units"
        ? 0.09
        : ["modifier", "inhibitor", "activator"].includes(edge.kind)
          ? 0.16
          : 0.5,
  );
  return { radii, distances, strengths, groups, spacing };
}
