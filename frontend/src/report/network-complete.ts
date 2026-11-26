import type { ReportIndex } from "@/report/index";
import { visualNode, relationStyle } from "@/report/network-style";
import type { NetworkEdge, NetworkNode, NetworkProjection, NetworkTheme } from "@/report/network";

/** Complete current report entry, including model definitions and referenced archive boundaries. */
export function completeNetwork(index: ReportIndex, theme: NetworkTheme): NetworkProjection {
  const nodes = new Map<string, NetworkNode>(),
    edges: NetworkEdge[] = [],
    unresolved: string[] = [];
  const addNode = (source: ReportIndex, pk: string) => {
    const element = source.get(pk) ?? source.nodes.get(pk);
    if (!element) return null;
    const node = visualNode(source, element, theme, source !== index);
    if (!nodes.has(node.id)) nodes.set(node.id, node);
    return node.id;
  };
  for (const pk of new Set([...index.nodes.keys(), ...index.elements.keys()])) addNode(index, pk);
  const pairs = new Set<string>(),
    authored = new Set<string>();
  const addEdge = (
    source: string,
    target: string,
    kind: string,
    entityId: string,
    external = false,
  ) => {
    if (!nodes.has(source) || !nodes.has(target)) return;
    const key = JSON.stringify([source, target, kind]);
    if (authored.has(key)) return;
    authored.add(key);
    pairs.add(JSON.stringify([source, target]));
    edges.push({
      id: key,
      entityId,
      source,
      target,
      kind,
      label: kind,
      external,
      ...relationStyle(kind, theme),
    });
  };
  for (const pk of index.nodes.keys()) {
    for (const edge of index.references(pk))
      addEdge(edge.source, edge.target, edge.kind, edge.source);
    for (const edge of index.referencesAcross(pk)) {
      const target = index.entry(edge.targetEntry),
        id = target ? addNode(target, edge.target) : null;
      if (id) addEdge(edge.source, id, edge.kind, id, true);
      else unresolved.push(`${edge.targetEntry}:${edge.target}`);
    }
    for (const edge of index.referencedAcross(pk)) {
      const source = index.entry(edge.sourceEntry),
        id = source ? addNode(source, edge.source) : null;
      if (id) addEdge(id, edge.target, edge.kind, id, true);
    }
  }
  // Containment is explicit tree ownership, drawn separately from biochemical relationships.
  const contains = (owner: string, child: string) => {
    if (owner !== child && !pairs.has(JSON.stringify([owner, child])))
      addEdge(owner, child, "contains", child);
  };
  const walk = (value: unknown, owner: string): void => {
    if (!value || typeof value !== "object") return;
    if (Array.isArray(value)) {
      for (const child of value) walk(child, owner);
      return;
    }
    let next = owner;
    if ("pk" in value && typeof value.pk === "string" && nodes.has(value.pk)) {
      contains(owner, value.pk);
      next = value.pk;
    }
    for (const child of Object.values(value)) if (typeof child === "object") walk(child, next);
  };
  walk(index.document, index.document.pk);
  for (const model of index.models) walk(model, index.document.pk);
  for (const definition of index.externalModelDefinitions) walk(definition, index.document.pk);
  return {
    scope: JSON.stringify([index.location, "document", "all"]),
    nodes: [...nodes.values()],
    edges,
    unresolved,
  };
}
