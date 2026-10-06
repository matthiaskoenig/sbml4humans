import { describe, expect, it } from "vitest";

import { HIGHLIGHT_LIMIT, highlight } from "@/report/highlight";

describe("highlight", () => {
  it("highlights the code of every format", async () => {
    for (const format of ["python", "julia", "r", "latex", "typst", "markdown"] as const) {
      const html = await highlight("x = 1  # <b>", format);
      expect(html).toContain("<pre");
      // the code is text, never markup
      expect(html).not.toContain("<b>");
    }
  });

  it("colours the tokens of the code", async () => {
    const html = await highlight("def f_dxdt(t, x, p):\n    return x  # rate", "python");
    // a keyword and a comment have colours of their own
    const colours = new Set(html?.match(/color:#[0-9A-Fa-f]{6}/g));
    expect(colours.size).toBeGreaterThan(2);
    const latex = await highlight("\\begin{align*} x &= 1 \\end{align*}", "latex");
    expect(new Set(latex?.match(/color:#[0-9A-Fa-f]{6}/g)).size).toBeGreaterThan(1);
  });

  it("leaves a code above the limit plain", async () => {
    expect(await highlight("x".repeat(HIGHLIGHT_LIMIT + 1), "python")).toBeNull();
  });
});
