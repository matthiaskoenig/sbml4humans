import {
  scenePacket,
  terminalPlacement,
  placeLabels,
  visibleCandidates,
  boundaryDistance,
} from "./decorations.js";
import { quadtree } from "d3-quadtree";

/** Pack visual instances without interpreting their domain objects. Colors use RGBA in 0..1. */
export function packScene(
  nodes,
  edges,
  { key = "", background = "#ffffff", foreground = "#222222" } = {},
) {
  const indices = new Map();
  const scene = {
    key,
    background,
    foreground,
    ids: [],
    entityIds: [],
    labels: [],
    labelPriorities: new Float32Array(nodes.length),
    positions: new Float32Array(nodes.length * 2),
    sizes: new Float32Array(nodes.length),
    shapes: new Float32Array(nodes.length),
    colors: new Float32Array(nodes.length * 4),
    strokeColors: new Float32Array(nodes.length * 4),
    strokeWidths: new Float32Array(nodes.length),
    links: new Float32Array(edges.length * 2),
    linkIds: [],
    linkColors: new Float32Array(edges.length * 4),
    linkWidths: new Float32Array(edges.length),
    linkStyles: new Float32Array(edges.length),
    linkArrows: [],
    startMarkers: [],
    endMarkers: [],
    linkLabels: [],
  };
  nodes.forEach((node, i) => {
    if (!node.id || indices.has(node.id))
      throw new Error(`Duplicate or empty visual id: ${node.id}`);
    if (![node.x, node.y].every(Number.isFinite))
      throw new Error(`Invalid coordinates: ${node.id}`);
    indices.set(node.id, i);
    scene.ids.push(node.id);
    scene.entityIds.push(node.entityId ?? node.id);
    scene.labels.push(node.label ?? node.id);
    scene.labelPriorities[i] = node.labelPriority ?? 1;
    scene.positions.set([node.x, node.y], i * 2);
    scene.sizes[i] = node.size ?? 14;
    scene.shapes[i] = node.shape ?? 0;
    scene.colors.set(node.color ?? [0.94, 0.94, 0.94, 1], i * 4);
    scene.strokeColors.set(node.strokeColor ?? [0.2, 0.2, 0.2, 1], i * 4);
    scene.strokeWidths[i] = node.strokeWidth ?? 1;
  });
  edges.forEach((edge, i) => {
    const source = indices.get(edge.source),
      target = indices.get(edge.target);
    if (source === undefined || target === undefined)
      throw new Error(`Unknown endpoint: ${edge.id}`);
    scene.links.set([source, target], i * 2);
    scene.linkIds.push(edge.entityId ?? edge.id);
    scene.linkColors.set(edge.color ?? [0.3, 0.3, 0.3, 1], i * 4);
    scene.linkWidths[i] = edge.width ?? 1;
    scene.linkStyles[i] = edge.style ?? 0;
    scene.linkArrows.push(edge.arrow ?? false);
    scene.startMarkers.push(edge.startMarker ?? "none");
    scene.endMarkers.push(edge.endMarker ?? (edge.arrow ? "triangle" : "none"));
    scene.linkLabels.push(edge.label ?? edge.id);
  });
  return scene;
}

/** Linear-time component layout for an initial view. Supplied scientific coordinates bypass it. */
export function layoutGraph(count, links, spacing = 100) {
  const adjacent = Array.from({ length: count }, () => []);
  for (let i = 0; i < links.length; i += 2) {
    const a = links[i],
      b = links[i + 1];
    adjacent[a].push(b);
    adjacent[b].push(a);
  }
  const positions = new Float32Array(count * 2),
    seen = new Uint8Array(count);
  let offsetX = 0,
    offsetY = 0,
    rowHeight = 0;
  const rowWidth = Math.max(800, Math.sqrt(count) * spacing * 1.8);
  for (let root = 0; root < count; root++) {
    if (seen[root]) continue;
    const queue = [root],
      depths = [0],
      levels = [];
    seen[root] = 1;
    for (let cursor = 0; cursor < queue.length; cursor++) {
      const node = queue[cursor],
        depth = depths[cursor];
      (levels[depth] ??= []).push(node);
      for (const neighbor of adjacent[node])
        if (!seen[neighbor]) {
          seen[neighbor] = 1;
          queue.push(neighbor);
          depths.push(depth + 1);
        }
    }
    const height = levels.reduce((largest, level) => Math.max(largest, level.length), 0) * spacing;
    const width = levels.length * spacing * 1.6;
    if (offsetX && offsetX + width > rowWidth) {
      offsetX = 0;
      offsetY += rowHeight + spacing;
      rowHeight = 0;
    }
    levels.forEach((level, depth) =>
      level.forEach((node, i) => {
        positions[node * 2] = offsetX + depth * spacing * 1.6;
        positions[node * 2 + 1] = offsetY + i * spacing + (height - level.length * spacing) / 2;
      }),
    );
    offsetX += width + spacing;
    rowHeight = Math.max(rowHeight, height);
  }
  return positions;
}

/** A controlled Cosmos view. Selection and color updates never rebuild topology or positions. */
export class CosmosViewer {
  constructor(container, { loadGraph, onSelect, onHover, onStatus, onVisible } = {}) {
    this.container = container;
    this.loadGraph = loadGraph ?? (async () => (await import("@cosmos.gl/graph")).Graph);
    this.onSelect = onSelect;
    this.onHover = onHover;
    this.onStatus = onStatus;
    this.onVisible = onVisible;
    this.generation = 0;
    this.destroyed = false;
    this.scene = null;
    this.selected = null;
    this.labelLimit = 160;
    this.showLabels = true;
    this.svg =
      container.ownerDocument?.createElementNS?.("http://www.w3.org/2000/svg", "svg") ?? null;
    if (this.svg) {
      this.svg.setAttribute("aria-hidden", "true");
      this.svg.setAttribute("data-testid", "viewer-labels");
      Object.assign(this.svg.style, {
        position: "absolute",
        inset: "0",
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: "1",
      });
      container.appendChild(this.svg);
    }
    this.measure = container.ownerDocument?.createElement?.("canvas").getContext("2d") ?? null;
    this.widths = new Map();
    this.observer = new ResizeObserver(() => {
      if (this.uploaded) {
        this.engine?.render(undefined, 0);
        this.scheduleDecorations();
      }
    });
    this.observer.observe(container);
  }

  async initialize() {
    if (this.initializing) return this.initializing;
    this.onStatus?.("loading");
    this.initializing = (async () => {
      const Graph = await this.loadGraph();
      if (this.destroyed) return null;
      const engine = new Graph(this.container, {
        enableSimulation: false,
        enableDrag: false,
        rescalePositions: false,
        fitViewOnInit: false,
        transitionDuration: 0,
        showFPSMonitor: false,
        backgroundColor: "#ffffff",
        pointDefaultSize: 14,
        pointSizeScale: 1,
        scalePointsOnZoom: false,
        scaleLinksOnZoom: false,
        curvedLinks: false,
        pointGreyoutOpacity: 0.45,
        linkGreyoutOpacity: 0.25,
        pointDefaultStrokeColor: "#333333",
        pointDefaultStrokeWidth: 1,
        outlinedPointRingColor: "#008b8b",
        hoveredPointRingColor: "#008b8b",
        renderHoveredPointRing: true,
        hoveredLinkWidthIncrease: 1.5,
        linkDefaultArrows: false,
        linkVisibilityMinTransparency: 1,
        onPointClick: (i, _position, event) => {
          if (this.uploaded) this.onSelect?.(this.pointEntity(i, event));
        },
        onLinkClick: (i) => {
          if (this.uploaded) this.onSelect?.(this.scene?.linkIds[i] ?? null);
        },
        onBackgroundClick: () => {
          if (this.uploaded) this.onSelect?.(null);
        },
        onPointMouseOver: (i) => {
          if (!this.uploaded) return;
          const owner = this.owners?.[i] ?? i;
          this.hovered = this.pointEntity(i);
          this.scheduleDecorations();
          this.onHover?.(
            owner >= 0
              ? (this.scene?.labels[owner] ?? "")
              : (this.scene?.linkLabels[-1 - owner] ?? ""),
            this.hovered,
          );
        },
        onPointMouseOut: () => {
          this.hovered = null;
          this.scheduleDecorations();
          this.onHover?.("");
        },
        onLinkMouseOver: (i) => {
          if (this.uploaded)
            this.onHover?.(this.scene?.linkLabels?.[i] ?? "", this.scene?.linkIds[i]);
        },
        onLinkMouseOut: () => this.onHover?.(""),
        onZoom: () => this.scheduleDecorations(),
        onZoomEnd: () => this.scheduleDecorations(),
      });
      this.engine = engine;
      await engine.ready;
      if (this.destroyed) return null;
      if (this.svg && this.svg.parentNode !== this.container) this.container.appendChild(this.svg);
      return engine;
    })();
    return this.initializing;
  }

  async setScene(scene, { labels = true, fit = true } = {}) {
    if (this.destroyed) return;
    const generation = ++this.generation;
    try {
      const engine = await this.initialize();
      if (!engine || this.destroyed || generation !== this.generation) return;
      engine.setConfigPartial({ backgroundColor: scene.background });
      const packet = scenePacket(scene, this.container.ownerDocument);
      this.packet = packet;
      this.showLabels = labels;
      this.markerScale = null;
      this.radiusScale = null;
      this.radii = new Float32Array(scene.ids.length);
      this.scene = scene;
      this.spatial = quadtree()
        .x((i) => scene.positions[i * 2])
        .y((i) => scene.positions[i * 2 + 1])
        .addAll(scene.ids.map((_, i) => i));
      this.owners = packet.owners;
      engine.setPointPositions(packet.positions, true);
      engine.setPointShapes(packet.shapes);
      engine.setPointSizes(packet.sizes);
      engine.setPointColors(packet.colors);
      engine.setPointStrokeColors(packet.strokeColors);
      engine.setPointStrokeWidths(packet.strokeWidths);
      engine.setImageData(packet.images);
      engine.setPointImageIndices(packet.imageIndices);
      engine.setPointImageSizes(packet.imageSizes);
      engine.setPointRenderOrder?.(
        Uint32Array.from({ length: packet.owners.length }, (_, i) =>
          i < packet.terminals.length ? scene.ids.length + i : i - packet.terminals.length,
        ),
      );
      engine.setLinks(scene.links);
      engine.setLinkColors(scene.linkColors);
      engine.setLinkWidths(scene.linkWidths);
      engine.setLinkStyles(scene.linkStyles);
      engine.setLinkArrows(scene.linkArrows.map(() => false));
      this.uploaded = true;
      this.setVisible(true);
      this.select(this.selected);
      engine.render(0, 0);
      if (fit) this.fit();
      this.scheduleDecorations();
      this.onStatus?.("ready");
    } catch (error) {
      if (!this.destroyed && generation === this.generation) {
        this.onStatus?.("failed", error);
        this.clear();
        this.engine?.destroy();
        this.engine = null;
        this.initializing = null;
      }
    }
  }

  pointEntity(index, event) {
    const owner = this.owners?.[index] ?? index;
    // Terminal sprite padding must never intercept a click inside a domain glyph.
    if (
      owner < 0 &&
      Number.isFinite(event?.clientX) &&
      this.spatial &&
      this.radii &&
      this.engine?.spaceToScreenPosition
    ) {
      const rect = this.container.getBoundingClientRect(),
        x = event.clientX - rect.left,
        y = event.clientY - rect.top;
      const origin = this.engine.spaceToScreenPosition([0, 0]),
        axis = this.engine.spaceToScreenPosition([1, 1]);
      const sx = axis[0] - origin[0],
        sy = axis[1] - origin[1];
      if (Math.abs(sx) > 1e-9 && Math.abs(sy) > 1e-9) {
        const wx = (x - origin[0]) / sx,
          wy = (y - origin[1]) / sy,
          range = this.maxRadius / Math.abs(sx);
        let hit = -1;
        this.spatial.visit((node, x0, y0, x1, y1) => {
          if (x0 > wx + range || x1 < wx - range || y0 > wy + range || y1 < wy - range) return true;
          if (!node.length) {
            let leaf = node;
            do {
              const i = leaf.data,
                dx = x - origin[0] - this.scene.positions[i * 2] * sx,
                dy = y - origin[1] - this.scene.positions[i * 2 + 1] * sy;
              if (
                this.scene.colors[i * 4 + 3] > 0 &&
                Math.hypot(dx, dy) <= boundaryDistance(this.scene.shapes[i], this.radii[i], dx, dy)
              )
                hit = Math.max(hit, i);
            } while ((leaf = leaf.next));
          }
          return false;
        });
        if (hit >= 0) return this.scene.entityIds[hit];
      }
    }
    return (owner >= 0 ? this.scene?.entityIds[owner] : this.scene?.linkIds[-1 - owner]) ?? null;
  }

  select(entityId) {
    this.selected = entityId;
    const engine = this.engine,
      scene = this.scene;
    if (!engine || !scene || !this.uploaded) return;
    const selected = new Set();
    scene.entityIds.forEach((id, i) => {
      if (id === entityId) selected.add(i);
    });
    const related = new Set(selected),
      links = [];
    for (let i = 0; i < scene.linkIds.length; i++) {
      const a = scene.links[i * 2],
        b = scene.links[i * 2 + 1];
      if (selected.has(a) || selected.has(b) || scene.linkIds[i] === entityId) {
        links.push(i);
        related.add(a);
        related.add(b);
      }
    }
    const points = [],
      outlines = [];
    const relatedLinks = new Set(links);
    (this.owners ?? scene.ids.map((_, i) => i)).forEach((owner, i) => {
      if (owner >= 0 ? related.has(owner) : relatedLinks.has(-1 - owner)) points.push(i);
      if (selected.has(owner) && i < scene.ids.length) outlines.push(i);
    });
    engine.setConfigPartial({
      highlightedPointIndices: related.size ? points : undefined,
      highlightedLinkIndices: related.size ? links : undefined,
      outlinedPointIndices: outlines.length ? outlines : undefined,
    });
    engine.render(undefined, 0);
    this.scheduleDecorations();
  }

  /** Metadata changes only text. It does not upload graph geometry or restart layout. */
  updateLabels(labels, visible = this.showLabels) {
    if (!this.scene || labels.length !== this.scene.ids.length) return;
    this.scene.labels = labels;
    this.showLabels = visible;
    this.scheduleDecorations();
  }

  scheduleDecorations() {
    if (
      this.frame ||
      this.destroyed ||
      !this.uploaded ||
      typeof requestAnimationFrame === "undefined"
    )
      return;
    this.frame = requestAnimationFrame(() => {
      this.frame = null;
      this.refreshDecorations();
    });
  }

  refreshDecorations() {
    const scene = this.scene,
      engine = this.engine;
    if (!this.uploaded || !scene || !engine?.spaceToScreenPosition) return;
    const origin = engine.spaceToScreenPosition([0, 0]),
      xAxis = engine.spaceToScreenPosition([1, 0]),
      yAxis = engine.spaceToScreenPosition([0, 1]);
    const sx = xAxis[0] - origin[0],
      sy = yAxis[1] - origin[1],
      scale = Math.abs(sx);
    if (!Number.isFinite(scale) || scale < 1e-9) return;
    if (
      this.radiusScale === null ||
      Math.abs(this.radiusScale - scale) > Math.max(1e-8, scale * 1e-6)
    ) {
      this.maxRadius = 0;
      for (let i = 0; i < scene.ids.length; i++) {
        const diameter = engine.getPointRadiusByIndex?.(i) ?? scene.sizes[i];
        this.radii[i] = engine.spaceToScreenRadius?.(diameter / 2) ?? diameter / 2;
        this.maxRadius = Math.max(this.maxRadius, this.radii[i]);
      }
      this.radiusScale = scale;
    }
    if (
      this.packet?.terminals.length &&
      (this.markerScale === null ||
        Math.abs(this.markerScale - scale) > Math.max(1e-8, scale * 1e-6))
    ) {
      const indices = [],
        positions = new Float32Array(this.packet.terminals.length * 2);
      let sizeChanged = false;
      this.packet.terminals.forEach((terminal, i) => {
        const p = terminalPlacement(scene, terminal.edge, terminal.end, scale, this.radii);
        const a = scene.links[terminal.edge * 2],
          b = scene.links[terminal.edge * 2 + 1];
        const distance =
          Math.hypot(
            scene.positions[a * 2] - scene.positions[b * 2],
            scene.positions[a * 2 + 1] - scene.positions[b * 2 + 1],
          ) * scale;
        indices.push(scene.ids.length + i);
        positions.set([p.x, p.y], i * 2);
        this.packet.positions.set([p.x, p.y], (scene.ids.length + i) * 2);
        const size =
          distance < this.radii[a] + this.radii[b] + 14 ||
          scene.linkColors[terminal.edge * 4 + 3] <= 0
            ? 0
            : terminal.size;
        if (this.packet.imageSizes[scene.ids.length + i] !== size) {
          this.packet.imageSizes[scene.ids.length + i] = size;
          sizeChanged = true;
        }
      });
      if (indices.length <= 64) engine.setPointPositionsByIndices(indices, positions);
      else engine.setPointPositions(this.packet.positions, true);
      if (sizeChanged) engine.setPointImageSizes(this.packet.imageSizes);
      engine.render(undefined, 0);
      this.markerScale = scale;
    }
    if (!this.svg) return;
    this.svg.replaceChildren();
    if (!this.showLabels) {
      if (this.visibleKey) {
        this.visibleKey = "";
        this.onVisible?.([]);
      }
      return;
    }
    const width = this.container.clientWidth,
      height = this.container.clientHeight,
      candidates = visibleCandidates(
        scene,
        { x: origin[0], y: origin[1], sx, sy },
        width,
        height,
        this.selected,
        this.hovered,
      );
    if (this.widths.size > 4096) this.widths.clear();
    if (this.measure) this.measure.font = "13px sans-serif";
    for (const candidate of candidates) {
      const i = candidate.index;
      let text = scene.labels[i];
      if (text.length > 36) text = `${text.slice(0, 35)}…`;
      if (!this.widths.has(text))
        this.widths.set(text, this.measure?.measureText(text).width ?? text.length * 7);
      candidate.text = text;
      candidate.width = this.widths.get(text);
    }
    const collides = (box, owner) => {
      if (!this.spatial) return false;
      const xa = (box.x - this.maxRadius - origin[0]) / sx,
        xb = (box.x + box.width + this.maxRadius - origin[0]) / sx;
      const ya = (box.y - this.maxRadius - origin[1]) / sy,
        yb = (box.y + box.height + this.maxRadius - origin[1]) / sy;
      const minX = Math.min(xa, xb),
        maxX = Math.max(xa, xb),
        minY = Math.min(ya, yb),
        maxY = Math.max(ya, yb);
      let found = false;
      this.spatial.visit((node, x0, y0, x1, y1) => {
        if (found || x0 > maxX || y0 > maxY || x1 < minX || y1 < minY) return true;
        if (!node.length) {
          let leaf = node;
          do {
            const i = leaf.data;
            if (i !== owner) {
              const x = origin[0] + scene.positions[i * 2] * sx,
                y = origin[1] + scene.positions[i * 2 + 1] * sy,
                r = this.radii[i] + 1;
              if (
                x + r > box.x &&
                x - r < box.x + box.width &&
                y + r > box.y &&
                y - r < box.y + box.height
              ) {
                found = true;
                break;
              }
            }
          } while ((leaf = leaf.next));
        }
        return found;
      });
      return found;
    };
    const labels = placeLabels(candidates, width, height, this.labelLimit, collides);
    const visible = labels.map((label) => scene.entityIds[label.index]);
    const visibleKey = visible.join("\0");
    if (this.visibleKey !== visibleKey) {
      this.visibleKey = visibleKey;
      this.onVisible?.(visible);
    }
    for (const label of labels) {
      const text = this.container.ownerDocument.createElementNS(
        "http://www.w3.org/2000/svg",
        "text",
      );
      text.setAttribute("x", label.x);
      text.setAttribute("y", label.y);
      text.setAttribute("font-size", "13");
      text.setAttribute("font-family", "sans-serif");
      text.setAttribute("fill", scene.foreground);
      text.setAttribute("stroke", scene.background);
      text.setAttribute("stroke-width", "3");
      text.setAttribute("paint-order", "stroke");
      text.setAttribute("data-entity", scene.entityIds[label.index]);
      text.textContent = label.text;
      this.svg.appendChild(text);
    }
  }

  updateColors(colors) {
    if (!this.scene || colors.length !== this.scene.colors.length)
      throw new Error("Point color count does not match the scene.");
    this.scene.colors = colors;
    const expanded = new Float32Array((this.owners?.length ?? this.scene.ids.length) * 4).fill(1);
    expanded.set(colors);
    this.engine?.setPointColors(expanded);
    this.engine?.render(undefined, 0);
  }

  setVisible(visible) {
    for (const canvas of this.container.querySelectorAll?.("canvas") ?? [])
      canvas.style.visibility = visible ? "visible" : "hidden";
  }

  /** Invalidate pending uploads and picking before changing a document or projection. */
  clear() {
    this.generation++;
    this.scene = null;
    this.owners = null;
    this.uploaded = false;
    this.packet = null;
    this.hovered = null;
    this.spatial = null;
    this.radii = null;
    this.svg?.replaceChildren();
    this.visibleKey = "";
    this.onVisible?.([]);
    this.setVisible(false);
    this.onHover?.("");
  }

  fit() {
    if (this.engine?.fitViewByPointIndices && this.scene)
      this.engine.fitViewByPointIndices(
        this.scene.ids.map((_, i) => i),
        0,
        0.12,
        false,
      );
    else this.engine?.fitView(0, 0.12, false);
  }
  zoom(factor) {
    if (this.engine) this.engine.setZoomLevel(this.engine.getZoomLevel() * factor, 0, false);
  }
  center(entityId) {
    const index = this.scene?.entityIds.indexOf(entityId) ?? -1;
    if (index >= 0)
      this.engine?.zoomToPointByIndex(
        index,
        0,
        Math.max(1, this.engine.getZoomLevel()),
        false,
        false,
      );
  }
  destroy() {
    this.clear();
    this.destroyed = true;
    this.observer.disconnect();
    if (this.frame) cancelAnimationFrame(this.frame);
    this.svg?.remove();
    this.widths.clear();
    this.engine?.destroy();
    this.engine = null;
    this.scene = null;
  }
}
