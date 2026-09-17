import katex from "katex";
import { describe, expect, it, vi } from "vitest";

import { MAX_LATEX_LENGTH, renderLatex } from "@/report/latex";

describe("renderLatex", () => {
  it("renders a short formula", () => {
    const html = renderLatex("\\frac{a}{b}");
    expect(html).not.toBeNull();
    expect(html).toContain("katex");
  });

  it("returns null for a formula longer than MAX_LATEX_LENGTH without calling KaTeX", () => {
    const spy = vi.spyOn(katex, "renderToString");
    const latex = "x+".repeat(MAX_LATEX_LENGTH);
    expect(latex.length).toBeGreaterThan(MAX_LATEX_LENGTH);
    expect(renderLatex(latex)).toBeNull();
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("renders a formula longer than MAX_LATEX_LENGTH when unlimited", () => {
    const latex = "x+".repeat(MAX_LATEX_LENGTH) + "x";
    expect(renderLatex(latex, { unlimited: true })).not.toBeNull();
  });

  it("returns null for deeply nested braces instead of throwing", () => {
    const latex = "{".repeat(5000) + "x" + "}".repeat(5000);
    expect(() => renderLatex(latex, { unlimited: true })).not.toThrow();
    expect(renderLatex(latex, { unlimited: true })).toBeNull();
  });

  it("does not render an href as a link", () => {
    const html = renderLatex("\\href{https://example.invalid}{x}");
    expect(html).not.toBeNull();
    expect(html).not.toContain("<a");
  });
});
