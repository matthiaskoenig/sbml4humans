import { describe, expect, it, vi } from "vitest";

import { MAX_SOURCE_BYTES, readSource } from "@/parsing/reader";

describe("browser source admission", () => {
  it("refuses an oversized file before reading or compiling it", async () => {
    const read = vi.fn();
    const file = { size: MAX_SOURCE_BYTES + 1, arrayBuffer: read } as unknown as File;
    await expect(readSource(file, new AbortController().signal)).rejects.toThrow("100 MB");
    expect(read).not.toHaveBeenCalled();
  });

  it("does not read a file whose load was already cancelled", async () => {
    const read = vi.fn();
    const file = { size: 20, arrayBuffer: read } as unknown as File;
    const controller = new AbortController();
    controller.abort();
    await expect(readSource(file, controller.signal)).rejects.toMatchObject({ name: "AbortError" });
    expect(read).not.toHaveBeenCalled();
  });
});
