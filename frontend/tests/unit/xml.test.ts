import { describe, expect, it } from "vitest";

import { tokenizeXml, valueParts, xmlLines } from "@/report/xml";

const kinds = (xml: string) => tokenizeXml(xml).map((token) => [token.kind, token.text]);

describe("tokenizeXml", () => {
  it("splits a tag into its punctuation, prefix, name, attributes and values", () => {
    expect(kinds('<rdf:li rdf:resource="https://x.org/a"/>')).toEqual([
      ["punct", "<"],
      ["prefix", "rdf:"],
      ["name", "li"],
      ["text", " "],
      ["prefix", "rdf:"],
      ["attribute", "resource"],
      ["punct", "="],
      ["value", '"https://x.org/a"'],
      ["punct", "/>"],
    ]);
  });

  it("tells the text, the entities, the closing tags and the other markup apart", () => {
    expect(kinds("<!-- c --><a x = 'v'>K&amp;Ö&#228;</a><?pi?><![CDATA[<b>]]>")).toEqual([
      ["markup", "<!-- c -->"],
      ["punct", "<"],
      ["name", "a"],
      ["text", " "],
      ["attribute", "x"],
      ["punct", " = "],
      ["value", "'v'"],
      ["punct", ">"],
      ["text", "K"],
      ["entity", "&amp;"],
      ["text", "Ö"],
      ["entity", "&#228;"],
      ["punct", "</"],
      ["name", "a"],
      ["punct", ">"],
      ["markup", "<?pi?>"],
      ["markup", "<![CDATA[<b>]]>"],
    ]);
  });

  it.each([
    "a < b & c",
    "<a b",
    '<a b="unclosed',
    "<a b c=d/ e>",
    "<!-- open",
    "<a <b>",
    "<:x/>",
    "</>",
    "&;",
  ])("keeps every character of malformed xml: %s", (xml) => {
    expect(
      tokenizeXml(xml)
        .map((token) => token.text)
        .join(""),
    ).toBe(xml);
  });

  it("scans a large input in linear time", () => {
    const xml = "<a b ".repeat(50_000);
    const start = performance.now();
    expect(
      tokenizeXml(xml)
        .map((token) => token.text)
        .join(""),
    ).toBe(xml);
    expect(performance.now() - start).toBeLessThan(1000);
  });
});

describe("xmlLines", () => {
  it("splits tokens at the lines and counts the indentation", () => {
    const lines = xmlLines("<a>\n  <!-- x\n  y -->\n\n    text</a>");
    expect(lines.map((line) => line.indent)).toEqual([0, 2, 2, 0, 4]);
    expect(lines[2]!.tokens).toEqual([{ kind: "markup", text: "  y -->" }]);
    expect(lines[3]!.tokens).toEqual([]);
  });
});

describe("valueParts", () => {
  it("breaks a url after its separators, not inside a word", () => {
    expect(valueParts('"https://identifiers.org/SBO:0000655"')).toEqual([
      '"https://',
      "identifiers.org/",
      'SBO:0000655"',
    ]);
    expect(valueParts('"a?b=1&c#d"')).toEqual(['"a?', "b=1&", "c#", 'd"']);
    expect(valueParts('"plain"')).toEqual(['"plain"']);
    expect(valueParts('"#meta_a"')).toEqual(['"#meta_a"']);
    expect(valueParts("'https://x.org/ns#'")).toEqual(["'https://", "x.org/", "ns#'"]);
  });
});
