import type { Node, SBase } from "@/api/types";
import type { ReportIndex } from "@/report/index";
import { elementLabel } from "@/report/label";
import type { NetworkNode, NetworkTheme } from "@/report/network";
import type { Color } from "@graphvis/viewer";

export function color(hex: string, alpha = 1): Color {
  return [
    parseInt(hex.slice(1, 3), 16) / 255,
    parseInt(hex.slice(3, 5), 16) / 255,
    parseInt(hex.slice(5, 7), 16) / 255,
    alpha,
  ];
}

/** The same SBML classes used by the report, with distinct shapes and restrained colours. */
const STYLES: Record<
  string,
  { shape: number; size: number; fill: string; stroke: string; priority: number }
> = {
  SBMLDocument: { shape: 5, size: 38, fill: "#dae9e7", stroke: "#315d5a", priority: 25 },
  Model: { shape: 5, size: 34, fill: "#bde4dc", stroke: "#26776c", priority: 30 },
  ExternalModelDefinition: { shape: 5, size: 28, fill: "#e4e5ef", stroke: "#666391", priority: 20 },
  Species: { shape: 0, size: 26, fill: "#f4f8fa", stroke: "#365c70", priority: 90 },
  QualitativeSpecies: { shape: 0, size: 26, fill: "#f4f8fa", stroke: "#365c70", priority: 90 },
  Reaction: { shape: 1, size: 14, fill: "#294b60", stroke: "#1e3847", priority: 70 },
  Transition: { shape: 1, size: 17, fill: "#294b60", stroke: "#1e3847", priority: 70 },
  Compartment: { shape: 5, size: 30, fill: "#e0efdc", stroke: "#5b8050", priority: 45 },
  Parameter: { shape: 3, size: 20, fill: "#dfecfa", stroke: "#487db5", priority: 45 },
  LocalParameter: { shape: 3, size: 17, fill: "#e9f0fa", stroke: "#6a8caf", priority: 30 },
  KineticLaw: { shape: 1, size: 21, fill: "#d9edf2", stroke: "#4d8997", priority: 50 },
  FunctionDefinition: { shape: 3, size: 23, fill: "#e7e0f2", stroke: "#8263a5", priority: 45 },
  AssignmentRule: { shape: 3, size: 23, fill: "#f2e4d0", stroke: "#aa7d3c", priority: 40 },
  RateRule: { shape: 3, size: 23, fill: "#f2e4d0", stroke: "#aa7d3c", priority: 40 },
  AlgebraicRule: { shape: 3, size: 23, fill: "#f2e4d0", stroke: "#aa7d3c", priority: 40 },
  InitialAssignment: { shape: 3, size: 21, fill: "#f5ead9", stroke: "#aa7d3c", priority: 35 },
  Event: { shape: 2, size: 27, fill: "#f3dedc", stroke: "#a6655b", priority: 50 },
  Constraint: { shape: 4, size: 24, fill: "#f3e4d9", stroke: "#a47146", priority: 35 },
  GeneProduct: { shape: 4, size: 24, fill: "#e6e0ef", stroke: "#806696", priority: 55 },
  UnitDefinition: { shape: 5, size: 20, fill: "#e8ecef", stroke: "#78838c", priority: 20 },
  SpeciesReference: { shape: 0, size: 11, fill: "#e8edf0", stroke: "#8b9aa4", priority: 10 },
  ModifierSpeciesReference: {
    shape: 0,
    size: 11,
    fill: "#e3e7f2",
    stroke: "#8494b4",
    priority: 10,
  },
  ListOf: { shape: 1, size: 12, fill: "#edf0f2", stroke: "#98a3ab", priority: 5 },
};

function compartmentOf(index: ReportIndex, element: SBase | undefined): string | null {
  if (!element) return null;
  if (element.sbmlType === "Compartment") return element.id ?? null;
  if ("compartment" in element && element.compartment) return element.compartment;
  if (element.sbmlType === "Reaction") {
    const locations = new Set<string>();
    for (const [role, references] of [
      ["reactant", element.listOfReactants ?? []],
      ["product", element.listOfProducts ?? []],
    ] as const)
      for (const reference of references) {
        const pk = index.resolve(reference.pk, role, reference.species),
          species = pk ? index.get(pk) : undefined;
        if (species && "compartment" in species && species.compartment)
          locations.add(species.compartment);
      }
    return locations.size === 1 ? [...locations][0]! : null;
  }
  const holder = index.holderOf(element.pk);
  return holder && holder !== element.pk ? compartmentOf(index, index.get(holder)) : null;
}

export function visualNode(
  index: ReportIndex,
  element: SBase | Node,
  theme: NetworkTheme,
  external = false,
): NetworkNode {
  const type = element.sbmlType ?? "SBase",
    dark = theme === "dark";
  const style = STYLES[type] ?? {
    shape: 4,
    size: 18,
    fill: "#e6e2ed",
    stroke: "#8a789e",
    priority: 20,
  };
  const actual = index.get(element.pk),
    owner = index.nodes.get(element.pk)?.model ?? (type === "Model" ? element.pk : null);
  const compartment = compartmentOf(index, actual);
  const reversible = actual?.sbmlType === "Reaction" && actual.reversible === true;
  return {
    id: external ? JSON.stringify([index.location, element.pk]) : element.pk,
    pk: element.pk,
    entry: index.location,
    model: index.modelIdOf(element.pk),
    element: actual,
    index,
    inspectable: index.has(element.pk),
    sbmlType: type,
    label: elementLabel(index, element.pk) || element.id || type,
    name: actual?.name ?? "",
    group: JSON.stringify([index.location, owner, compartment ?? ""]),
    external,
    x: 0,
    y: 0,
    shape: style.shape,
    size: style.size,
    labelPriority: style.priority,
    color: color(reversible ? (dark ? "#679fa7" : "#4e7e84") : dark ? style.stroke : style.fill),
    strokeColor: color(dark ? style.fill : style.stroke),
    strokeWidth: reversible ? 2.2 : 1.5,
  };
}

export function relationStyle(kind: string, theme: NetworkTheme) {
  const dark = theme === "dark";
  if (kind === "contains")
    return { color: color(dark ? "#7c8e9c" : "#9cabb5", 0.38), width: 0.8, style: 2, arrow: false };
  if (kind === "math")
    return { color: color(dark ? "#d4ae67" : "#a47c3d", 0.75), width: 1.1, style: 2, arrow: true };
  if (kind === "units")
    return { color: color(dark ? "#929eaa" : "#9ba6ae", 0.55), width: 0.9, style: 1, arrow: false };
  if (["reactant", "product"].includes(kind))
    return {
      color: color(dark ? "#cfdae2" : "#4b6070"),
      width: 1.5,
      style: 0,
      arrow: kind === "product",
    };
  return { color: color(dark ? "#a1b6c6" : "#8196a5", 0.75), width: 1.1, style: 0, arrow: true };
}
