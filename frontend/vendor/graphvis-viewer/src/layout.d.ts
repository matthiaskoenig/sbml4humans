/** Compute a static layout off the UI thread. Does not change the endpoint buffer. */
export interface LayoutOptions {
  radii?: Float32Array;
  distances?: Float32Array;
  strengths?: Float32Array;
  groups?: Uint32Array;
  spacing?: number;
}
export function computeLayout(
  count: number,
  links: Float32Array,
  options?: LayoutOptions,
): Float32Array;
