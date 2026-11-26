import { forceSimulation, forceLink, forceManyBody, forceCollide, forceX, forceY } from "d3-force";

/** Size-aware force layout with role-specific springs and deterministic component packing. */
export function computeLayout(count, links, options = {}) {
  if (!Number.isInteger(count) || count < 0 || links.length % 2)
    throw new Error("Invalid layout dimensions.");
  const { radii, distances, strengths, groups, spacing = 1 } = options;
  if (!Number.isFinite(spacing) || spacing <= 0) throw new Error("Invalid layout spacing.");
  for (const values of [radii, distances, strengths])
    if (values)
      for (const value of values) {
        if (!Number.isFinite(value) || value < 0) throw new Error("Invalid layout hint.");
      }
  for (const [values, length] of [
    [radii, count],
    [groups, count],
    [distances, links.length / 2],
    [strengths, links.length / 2],
  ]) {
    if (values && values.length !== length) throw new Error("Layout hints do not match the graph.");
  }
  const parent = Uint32Array.from({ length: count }, (_, i) => i),
    degree = new Uint32Array(count);
  const find = (i) => {
    while (parent[i] !== i) {
      parent[i] = parent[parent[i]];
      i = parent[i];
    }
    return i;
  };
  const pairs = new Map();
  for (let i = 0; i < links.length; i += 2) {
    const a = links[i],
      b = links[i + 1];
    if (!Number.isInteger(a) || !Number.isInteger(b) || a < 0 || b < 0 || a >= count || b >= count)
      throw new Error("Invalid layout endpoint.");
    parent[find(b)] = find(a);
    const key = a < b ? `${a}:${b}` : `${b}:${a}`;
    if (!pairs.has(key)) {
      degree[a]++;
      degree[b]++;
    }
    pairs.set(key, (pairs.get(key) ?? 0) + 1);
  }
  const components = new Map();
  for (let i = 0; i < count; i++) {
    const key = find(i);
    if (!components.has(key)) components.set(key, { ids: [], edges: [], first: i });
    components.get(key).ids.push(i);
  }
  for (let i = 0; i < links.length / 2; i++) components.get(find(links[i * 2])).edges.push(i);
  const result = new Float32Array(count * 2),
    layouts = [];
  for (const component of components.values()) {
    const nodes = component.ids.map((id) => ({
      id,
      radius: Math.max(4, radii?.[id] ?? 14) * spacing,
    }));
    const byId = new Map(nodes.map((node) => [node.id, node]));
    if (nodes.length === 1) {
      nodes[0].x = 0;
      nodes[0].y = 0;
    } else {
      const springs = new Map();
      for (const i of component.edges) {
        const a = links[i * 2],
          b = links[i * 2 + 1],
          key = a < b ? `${a}:${b}` : `${b}:${a}`;
        const weight = strengths?.[i] ?? 0.35,
          distance = (distances?.[i] ?? 100) * spacing;
        if (!springs.has(key))
          springs.set(key, {
            source: byId.get(a),
            target: byId.get(b),
            strength: weight,
            total: weight * distance,
            weight,
          });
        else {
          const spring = springs.get(key);
          spring.strength = Math.max(spring.strength, weight);
          spring.total += weight * distance;
          spring.weight += weight;
        }
      }
      const edges = [...springs.values()].map((edge) => ({
        ...edge,
        distance: edge.weight ? edge.total / edge.weight : 100 * spacing,
        strength:
          edge.strength /
          Math.pow(Math.max(degree[edge.source.id], degree[edge.target.id], 1), 0.25),
      }));
      const groupIds = [...new Set(nodes.map((node) => groups?.[node.id] ?? 0))].sort(
        (a, b) => a - b,
      );
      const anchors = new Map(
        groupIds.map((group, i) => [
          group,
          {
            x:
              Math.cos((i * 2 * Math.PI) / groupIds.length) *
              Math.sqrt(nodes.length) *
              24 *
              spacing,
            y:
              Math.sin((i * 2 * Math.PI) / groupIds.length) *
              Math.sqrt(nodes.length) *
              24 *
              spacing,
          },
        ]),
      );
      const baseTicks = nodes.length > 20000 ? 55 : nodes.length > 2000 ? 150 : 300;
      const ticks = Math.max(
        20,
        Math.min(baseTicks, Math.floor(4000000 / (nodes.length * 3 + edges.length))),
      );
      const simulation = forceSimulation(nodes)
        .stop()
        .alphaDecay(1 - Math.pow(0.015, 1 / ticks))
        .force(
          "links",
          forceLink(edges)
            .distance((edge) =>
              Math.max(edge.distance, edge.source.radius + edge.target.radius + 22),
            )
            .strength((edge) => edge.strength),
        )
        .force(
          "charge",
          forceManyBody()
            .strength((node) => -110 - node.radius * node.radius * 1.6)
            .theta(0.9),
        )
        .force("collision", forceCollide((node) => node.radius + 10 * spacing).iterations(3))
        .force(
          "x",
          forceX((node) =>
            groupIds.length > 1 ? anchors.get(groups?.[node.id] ?? 0).x : 0,
          ).strength(groupIds.length > 1 ? 0.025 : 0.008),
        )
        .force(
          "y",
          forceY((node) =>
            groupIds.length > 1 ? anchors.get(groups?.[node.id] ?? 0).y : 0,
          ).strength(groupIds.length > 1 ? 0.025 : 0.008),
        );
      simulation.tick(ticks);
    }
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    for (const node of nodes) {
      minX = Math.min(minX, node.x - node.radius);
      minY = Math.min(minY, node.y - node.radius);
      maxX = Math.max(maxX, node.x + node.radius);
      maxY = Math.max(maxY, node.y + node.radius);
    }
    layouts.push({ ...component, nodes, minX, minY, width: maxX - minX, height: maxY - minY });
  }
  layouts.sort((a, b) => b.height - a.height || b.width - a.width || a.first - b.first);
  const gap = 64 * spacing;
  const area = layouts.reduce((sum, item) => sum + (item.width + gap) * (item.height + gap), 0);
  const rowWidth = Math.max(400, Math.sqrt(area) * 1.3);
  let x = 0,
    y = 0,
    height = 0;
  for (const item of layouts) {
    if (x && x + item.width > rowWidth) {
      x = 0;
      y += height + gap;
      height = 0;
    }
    for (const node of item.nodes)
      result.set([x + node.x - item.minX, y + node.y - item.minY], node.id * 2);
    x += item.width + gap;
    height = Math.max(height, item.height);
  }
  return result;
}
