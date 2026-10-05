import { describe, expect, it } from "vitest";

import { CHUNK_SIZE_LIMIT, chunkSizeLimit } from "../../chunkSizeLimit";

type Output =
  { type: "chunk"; fileName: string; code: string } | { type: "asset"; fileName: string };

/** Run the check of the plugin over a bundle, the message of the error it raises or null. */
function check(bundle: Output[], limit?: number): string | null {
  const plugin = chunkSizeLimit(limit);
  const generate = plugin.generateBundle as unknown as (
    this: { error: (message: string) => never },
    options: unknown,
    bundle: Record<string, Output>,
  ) => void;
  try {
    generate.call(
      {
        error: (message: string) => {
          throw new Error(message);
        },
      },
      {},
      Object.fromEntries(bundle.map((output) => [output.fileName, output])),
    );
    return null;
  } catch (error) {
    return (error as Error).message;
  }
}

const chunk = (fileName: string, size: number): Output => ({
  type: "chunk",
  fileName,
  code: "x".repeat(size),
});

describe("chunkSizeLimit", () => {
  it("fails the build at 500 kB", () => {
    expect(CHUNK_SIZE_LIMIT).toBe(500);
    expect(chunkSizeLimit().apply).toBe("build");
  });

  it("passes chunks up to the limit and every asset", () => {
    expect(
      check([
        chunk("assets/index.js", 500_000),
        { type: "asset", fileName: "assets/glossary-details.json" },
      ]),
    ).toBeNull();
  });

  it("names every chunk beyond the limit with its size", () => {
    const message = check([
      chunk("assets/ReportPage.js", 500_001),
      chunk("assets/index.js", 1_000),
      chunk("assets/katex.js", 612_300),
    ]);
    expect(message).toContain("assets/ReportPage.js (500.0 kB)");
    expect(message).toContain("assets/katex.js (612.3 kB)");
    expect(message).not.toContain("index.js");
  });

  it("takes another limit", () => {
    expect(check([chunk("assets/index.js", 2_000)], 1)).toContain("larger than 1 kB");
  });
});
