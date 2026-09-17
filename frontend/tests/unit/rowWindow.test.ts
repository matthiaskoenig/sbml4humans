import { describe, expect, it } from "vitest";

import { rowWindow } from "@/report/rowWindow";

const ROW = 36;
const VIEWPORT = ROW * 15;

describe("rowWindow", () => {
  it("renders the first rows at the top", () => {
    expect(rowWindow(0, 1000, ROW, VIEWPORT, 5)).toEqual({
      start: 0,
      end: 20,
      before: 0,
      after: 980 * ROW,
    });
  });

  it("starts the window at the partially visible row", () => {
    expect(rowWindow(50, 1000, ROW, VIEWPORT, 5)).toMatchObject({ start: 0, end: 21 });
  });

  it("renders the rows in view with the overscan in the middle", () => {
    expect(rowWindow(ROW * 500, 1000, ROW, VIEWPORT, 5)).toEqual({
      start: 495,
      end: 520,
      before: 495 * ROW,
      after: 480 * ROW,
    });
  });

  it("ends at the last row", () => {
    expect(rowWindow(ROW * 1000 - VIEWPORT, 1000, ROW, VIEWPORT, 5)).toEqual({
      start: 980,
      end: 1000,
      before: 980 * ROW,
      after: 0,
    });
  });

  it("renders every row of a list shorter than the viewport", () => {
    expect(rowWindow(0, 10, ROW, VIEWPORT, 5)).toEqual({ start: 0, end: 10, before: 0, after: 0 });
  });

  it("keeps the height of the list for every scroll position", () => {
    for (const scrollTop of [-10, 0, 1, 35, 36, 7000, 35460, 36000, 99999]) {
      const { start, end, before, after } = rowWindow(scrollTop, 1000, ROW, VIEWPORT, 5);
      expect(start).toBeLessThanOrEqual(end);
      expect(before + (end - start) * ROW + after).toBe(1000 * ROW);
    }
  });
});
