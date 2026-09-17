/** The rows of a windowed table to render and the spacers around them. */
export interface RowWindow {
  /** Index of the first rendered row. */
  start: number;
  /** Index after the last rendered row. */
  end: number;
  /** Height of the spacer before the first rendered row. */
  before: number;
  /** Height of the spacer after the last rendered row. */
  after: number;
}

/** The window of a list of `total` rows of `rowHeight` in a viewport of `viewportHeight`
 * scrolled to `scrollTop`, with `overscan` rows more on each side. The rows have a fixed
 * height, so the window follows from the scroll position without measuring. */
export function rowWindow(
  scrollTop: number,
  total: number,
  rowHeight: number,
  viewportHeight: number,
  overscan: number,
): RowWindow {
  const first = Math.floor(Math.max(0, scrollTop) / rowHeight);
  const start = Math.min(total, Math.max(0, first - overscan));
  const end = Math.max(
    start,
    Math.min(total, first + Math.ceil(viewportHeight / rowHeight) + overscan),
  );
  return { start, end, before: start * rowHeight, after: (total - end) * rowHeight };
}
