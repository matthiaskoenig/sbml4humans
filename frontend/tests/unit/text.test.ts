import { describe, expect, it } from "vitest";

import { isHttpUrl } from "@/report/text";

describe("isHttpUrl", () => {
  it.each([
    ["http://example.org/model.xml", true],
    ["https://example.org/model.xml", true],
    ["HTTPS://EXAMPLE.ORG/model.xml", true],
    ["  https://example.org/model.xml", true],
    ["https://example.org/model.xml\n", true],
    ["javascript:alert(1)", false],
    ["  javascript:alert(1)", false],
    ["//example.org/model.xml", false],
    ["urn:miriam:uniprot:P12345", false],
    ["", false],
    ["   ", false],
    [null, false],
    [undefined, false],
  ])("reads %o as %s", (text, expected) => {
    expect(isHttpUrl(text)).toBe(expected);
  });
});
