import { describe, expect, it } from "vitest";

import { decodeReferences } from "@/report/text";

describe("decodeReferences", () => {
  it("decodes the numeric character references of the report", () => {
    expect(decodeReferences("X &#10142; Y")).toBe("X ➞ Y");
  });

  it("leaves text without references unchanged", () => {
    expect(decodeReferences("plain text")).toBe("plain text");
  });
});
