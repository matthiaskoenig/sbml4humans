export type Color = readonly [number, number, number, number];
export type Marker = "none" | "triangle" | "bar" | "circle" | "diamond";
export interface VisualNode {
  id: string;
  entityId?: string;
  label?: string;
  labelPriority?: number;
  x: number;
  y: number;
  size?: number;
  shape?: number;
  color?: Color;
  strokeColor?: Color;
  strokeWidth?: number;
}
export interface VisualEdge {
  id: string;
  entityId?: string;
  source: string;
  target: string;
  color?: Color;
  width?: number;
  style?: number;
  arrow?: boolean;
  label?: string;
  startMarker?: Marker;
  endMarker?: Marker;
}
export interface Scene {
  key: string;
  background: string;
  foreground: string;
  ids: string[];
  entityIds: string[];
  labels: string[];
  labelPriorities: Float32Array;
  positions: Float32Array;
  sizes: Float32Array;
  shapes: Float32Array;
  colors: Float32Array;
  strokeColors: Float32Array;
  strokeWidths: Float32Array;
  links: Float32Array;
  linkIds: string[];
  linkColors: Float32Array;
  linkWidths: Float32Array;
  linkStyles: Float32Array;
  linkArrows: boolean[];
  startMarkers: Marker[];
  endMarkers: Marker[];
  linkLabels: string[];
}
export interface ViewerOptions {
  loadGraph?: () => Promise<unknown>;
  onSelect?: (entityId: string | null) => void;
  onHover?: (label: string, entityId?: string | null) => void;
  onStatus?: (status: "loading" | "ready" | "failed", error?: unknown) => void;
  onVisible?: (entityIds: string[]) => void;
}
export function packScene(
  nodes: readonly VisualNode[],
  edges: readonly VisualEdge[],
  options?: { key?: string; background?: string; foreground?: string },
): Scene;
export function layoutGraph(count: number, links: Float32Array, spacing?: number): Float32Array;
export class CosmosViewer {
  constructor(container: HTMLElement, options?: ViewerOptions);
  setScene(scene: Scene, options?: { labels?: boolean; fit?: boolean }): Promise<void>;
  clear(): void;
  select(entityId: string | null): void;
  updateColors(colors: Float32Array): void;
  updateLabels(labels: string[], visible?: boolean): void;
  fit(): void;
  zoom(factor: number): void;
  center(entityId: string): void;
  destroy(): void;
}
