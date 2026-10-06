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

  it("returns null when the normalised latex exceeds MAX_LATEX_LENGTH, even though the raw latex does not", () => {
    // every micro sign expands to "\mu " (4 characters), so this string is under the cap before
    // normalisation and over it after.
    const latex = "\u00b5".repeat(MAX_LATEX_LENGTH - 10);
    expect(latex.length).toBeLessThan(MAX_LATEX_LENGTH);
    const spy = vi.spyOn(katex, "renderToString");
    expect(renderLatex(latex)).toBeNull();
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("renders such a latex when unlimited", () => {
    const latex = "\u00b5".repeat(MAX_LATEX_LENGTH - 10);
    expect(renderLatex(latex, { unlimited: true })).not.toBeNull();
  });

  it("renders the links of the symbols of an equation with links", () => {
    const html = renderLatex("\\htmlData{pk=m/Species:S}{S} + 1", { links: true });
    expect(html).toContain('data-pk="m/Species:S"');
  });

  it("renders no link without the option", () => {
    const html = renderLatex("\\htmlData{pk=m/Species:S}{S}");
    expect(html).not.toBeNull();
    expect(html).not.toContain("data-pk");
  });

  it("trusts nothing but the pk of htmlData with links", () => {
    for (const latex of [
      "\\href{https://example.invalid}{x}",
      "\\url{https://example.invalid}",
      "\\htmlClass{evil}{x}",
      "\\htmlStyle{color:red}{x}",
      "\\htmlId{x}{x}",
    ]) {
      const html = renderLatex(latex, { links: true });
      expect(html).not.toBeNull();
      expect(html).not.toContain("<a");
      expect(html).not.toContain("evil");
      expect(html).not.toContain("color:red");
      expect(html).not.toContain('id="x"');
    }
    const other = renderLatex("\\htmlData{onclick=alert(1)}{x}", { links: true });
    expect(other).not.toContain("data-onclick");
  });
});
