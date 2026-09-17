import { describe, expect, it } from "vitest";

import { parseQuery, toQuery } from "@/report/query";

describe("view state query", () => {
  it("parses an empty query into the defaults", () => {
    expect(parseQuery({})).toEqual({ entry: null, model: null, pk: null, q: "", types: null });
  });

  it("parses every parameter", () => {
    expect(
      parseQuery({
        entry: "./model.xml",
        model: "m1",
        pk: "m1/Species:s1",
        q: "laci",
        types: "Species,Reaction",
      }),
    ).toEqual({
      entry: "./model.xml",
      model: "m1",
      pk: "m1/Species:s1",
      q: "laci",
      types: ["Species", "Reaction"],
    });
  });

  it("drops unknown types and takes the first of repeated parameters", () => {
    expect(parseQuery({ types: "Species,Nope", pk: ["a", "b"] })).toMatchObject({
      types: ["Species"],
      pk: "a",
    });
    expect(parseQuery({ types: "Nope" }).types).toEqual([]);
  });

  it("writes only the non default values", () => {
    expect(toQuery({ entry: null, model: null, pk: null, q: "", types: null })).toEqual({});
    expect(toQuery({ entry: "./m.xml", model: "m", pk: "p", q: "x", types: ["Species"] })).toEqual({
      entry: "./m.xml",
      model: "m",
      pk: "p",
      q: "x",
      types: "Species",
    });
  });

  it("round trips", () => {
    const state = {
      entry: "./a b.xml",
      model: "m",
      pk: "m/Species:s 1",
      q: "a&b",
      types: ["Species" as const],
    };
    expect(parseQuery(toQuery(state) as Record<string, string>)).toEqual(state);
  });
});
