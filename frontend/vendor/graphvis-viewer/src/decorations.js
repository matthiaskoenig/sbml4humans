/** Distance along a ray to a glyph outline, in screen pixels. */
export function boundaryDistance(shape, radius, dx, dy) {
  const length = Math.hypot(dx, dy) || 1,
    x = Math.abs(dx / length),
    y = Math.abs(dy / length);
  if (shape === 1) return radius / Math.max(x, y, 1e-9);
  if (shape === 3) return radius / Math.max(x + y, 1e-9);
  return radius;
}

/** A terminal's tip is clipped to its glyph. Its atlas sprite is centred behind that tip. */
export function terminalPlacement(scene, edge, end, scale, radii) {
  const a = scene.links[edge * 2],
    b = scene.links[edge * 2 + 1];
  const owner = end ? b : a,
    other = end ? a : b;
  const dx = scene.positions[owner * 2] - scene.positions[other * 2],
    dy = scene.positions[owner * 2 + 1] - scene.positions[other * 2 + 1];
  const length = Math.hypot(dx, dy);
  if (length < 1e-9) return null;
  const type = (end ? scene.endMarkers : scene.startMarkers)[edge];
  if (!type || type === "none") return null;
  const size = 20,
    inset =
      (size * (type === "triangle" ? 10 : type === "circle" ? 7 : type === "diamond" ? 8 : 0)) / 32;
  const distance =
    (boundaryDistance(scene.shapes[owner], radii?.[owner] ?? scene.sizes[owner] / 2, dx, dy) +
      2 +
      inset) /
    Math.max(scale, 1e-9);
  return {
    x: scene.positions[owner * 2] - (dx / length) * distance,
    y: scene.positions[owner * 2 + 1] - (dy / length) * distance,
    angle: Math.atan2(-dy, dx),
    type,
    size,
    edge,
  };
}

function markerImage(document, marker, color, background) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 32;
  const c = canvas.getContext("2d");
  if (!c) throw new Error("Canvas is unavailable for endpoint glyphs.");
  c.translate(16, 16);
  c.rotate(marker.angle);
  c.lineWidth = 3;
  c.strokeStyle = color;
  c.fillStyle = color;
  c.beginPath();
  if (marker.type === "triangle") {
    c.moveTo(10, 0);
    c.lineTo(-8, -6);
    c.lineTo(-8, 6);
    c.closePath();
    c.fill();
  } else if (marker.type === "bar") {
    c.moveTo(0, -9);
    c.lineTo(0, 9);
    c.stroke();
  } else if (marker.type === "diamond") {
    c.moveTo(8, 0);
    c.lineTo(0, -7);
    c.lineTo(-8, 0);
    c.lineTo(0, 7);
    c.closePath();
    c.fill();
  } else {
    c.arc(0, 0, 7, 0, Math.PI * 2);
    c.fillStyle = background;
    c.fill();
    c.stroke();
  }
  return c.getImageData(0, 0, 32, 32);
}

/** Expand render-only terminal sprites without adding domain entities or graph links. */
export function scenePacket(scene, document) {
  const terminals = [];
  for (let edge = 0; edge < scene.linkIds.length; edge++)
    for (const end of [false, true]) {
      const terminal = terminalPlacement(scene, edge, end, 1);
      if (terminal) terminals.push({ ...terminal, end });
    }
  const count = scene.ids.length,
    total = count + terminals.length;
  const expand = (values, stride) => {
    const array = new Float32Array(total * stride);
    array.set(values);
    return array;
  };
  const packet = {
    positions: expand(scene.positions, 2),
    shapes: expand(scene.shapes, 1),
    sizes: expand(scene.sizes, 1),
    colors: expand(scene.colors, 4),
    strokeColors: expand(scene.strokeColors, 4),
    strokeWidths: expand(scene.strokeWidths, 1),
    imageIndices: new Float32Array(total).fill(-1),
    imageSizes: new Float32Array(total),
    images: [],
    terminals,
    owners: Array.from({ length: total }, (_, i) =>
      i < count ? i : -1 - terminals[i - count].edge,
    ),
  };
  terminals.forEach((terminal, i) => {
    const p = count + i;
    packet.positions.set([terminal.x, terminal.y], p * 2);
    packet.shapes[p] = 8;
    packet.imageSizes[p] = terminal.size;
  });
  refreshPalette(scene, packet, document);
  return packet;
}

/** Reuse geometry and terminal ownership when only the palette changes. */
export function refreshPalette(scene, packet, document) {
  packet.colors.set(scene.colors);
  packet.strokeColors.set(scene.strokeColors);
  packet.images = [];
  const images = new Map();
  packet.terminals.forEach((terminal, i) => {
    const color = `rgba(${Array.from(scene.linkColors.subarray(terminal.edge * 4, terminal.edge * 4 + 3), (c) => Math.round(c * 255)).join(",")},${scene.linkColors[terminal.edge * 4 + 3]})`;
    const angle = (Math.round((terminal.angle / (Math.PI * 2)) * 64) / 64) * Math.PI * 2;
    const key = `${terminal.type}:${color}:${angle}`;
    if (!images.has(key)) {
      images.set(key, packet.images.length);
      packet.images.push(markerImage(document, { ...terminal, angle }, color, scene.background));
    }
    const p = scene.ids.length + i;
    packet.colors.set([1, 1, 1, 1], p * 4);
    packet.imageIndices[p] = images.get(key);
  });
}

/** Place high-priority labels first. A spatial grid bounds collision checks. */
export function placeLabels(candidates, width, height, limit = 160, collides) {
  const cells = new Map(),
    result = [],
    cellSize = 48;
  const keys = (box) => {
    const keys = [];
    for (let x = Math.floor(box.x / cellSize); x <= Math.floor((box.x + box.width) / cellSize); x++)
      for (
        let y = Math.floor(box.y / cellSize);
        y <= Math.floor((box.y + box.height) / cellSize);
        y++
      )
        keys.push(`${x}:${y}`);
    return keys;
  };
  const intersects = (a, b) =>
    a.x < b.x + b.width + 3 &&
    a.x + a.width + 3 > b.x &&
    a.y < b.y + b.height + 3 &&
    a.y + a.height + 3 > b.y;
  const add = (box) => {
    for (const key of keys(box)) {
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push(box);
    }
  };
  // Glyphs also reserve space, so text cannot conceal another object.
  for (const c of candidates)
    add({
      x: c.x - c.radius,
      y: c.y - c.radius,
      width: c.radius * 2,
      height: c.radius * 2,
      owner: c.index,
    });
  for (const c of [...candidates].sort((a, b) => b.priority - a.priority || a.index - b.index)) {
    const locations = [
      [c.x + c.radius + 5, c.y - 8],
      [c.x - c.radius - c.width - 5, c.y - 8],
      [c.x - c.width / 2, c.y + c.radius + 5],
      [c.x - c.width / 2, c.y - c.radius - 19],
    ];
    for (const [x, y] of locations) {
      const box = { x, y, width: c.width, height: 16, owner: c.index };
      if (x < 3 || y < 3 || x + c.width > width - 3 || y + 16 > height - 3) continue;
      if (
        keys(box).some((key) =>
          (cells.get(key) ?? []).some((other) => other.owner !== c.index && intersects(box, other)),
        )
      )
        continue;
      if (collides?.(box, c.index)) continue;
      result.push({ ...c, x, y: y + 12 });
      add(box);
      break;
    }
    if (result.length >= limit) break;
  }
  return result;
}

/** Keep viewport label work bounded, including selected objects beyond the initial label set. */
export function visibleCandidates(
  scene,
  transform,
  width,
  height,
  selected,
  hovered,
  limit = 2000,
  radii,
) {
  const heap = [],
    worse = (a, b) => a.priority < b.priority || (a.priority === b.priority && a.index > b.index);
  const down = () => {
    let i = 0;
    for (;;) {
      let child = i * 2 + 1;
      if (child >= heap.length) break;
      if (child + 1 < heap.length && worse(heap[child + 1], heap[child])) child++;
      if (!worse(heap[child], heap[i])) break;
      [heap[i], heap[child]] = [heap[child], heap[i]];
      i = child;
    }
  };
  for (let i = 0; i < scene.ids.length; i++) {
    const x = transform.x + scene.positions[i * 2] * transform.sx,
      y = transform.y + scene.positions[i * 2 + 1] * transform.sy;
    if (x < 0 || y < 0 || x > width || y > height) continue;
    const priority =
      scene.entityIds[i] === selected
        ? 1e7
        : scene.entityIds[i] === hovered
          ? 1e6
          : scene.labelPriorities[i];
    if (
      heap.length >= limit &&
      (priority < heap[0].priority || (priority === heap[0].priority && i > heap[0].index))
    )
      continue;
    const item = {
      index: i,
      x,
      y,
      radius: radii?.[i] ?? scene.sizes[i] / 2,
      priority,
    };
    if (heap.length < limit) {
      heap.push(item);
      let k = heap.length - 1;
      while (k) {
        const parent = (k - 1) >> 1;
        if (!worse(heap[k], heap[parent])) break;
        [heap[k], heap[parent]] = [heap[parent], heap[k]];
        k = parent;
      }
    } else if (worse(heap[0], item)) {
      heap[0] = item;
      down();
    }
  }
  return heap;
}
