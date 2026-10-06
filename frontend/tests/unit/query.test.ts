import { describe, expect, it } from "vitest";

import { parseQuery, toQuery } from "@/report/query";

describe("view state query", () => {
  it("parses an empty query into the defaults", () => {
    expect(parseQuery({})).toEqual({
      entry: null,
      model: null,
      pk: null,
      q: "",
      types: null,
      help: null,
      view: "tables",
    });
  });

  it("parses every parameter", () => {
    expect(
      parseQuery({
        entry: "./model.xml",
        model: "m1",
        pk: "m1/Species:s1",
        q: "laci",
        types: "Species,Reaction",
        help: "types/Species",
        view: "equations",
      }),
    ).toEqual({
      entry: "./model.xml",
      model: "m1",
      pk: "m1/Species:s1",
      q: "laci",
      types: ["Species", "Reaction"],
      help: "types/Species",
      view: "equations",
    });
  });

  it("drops unknown types and takes the first of repeated parameters", () => {
    expect(parseQuery({ types: "Species,Nope", pk: ["a", "b"] })).toMatchObject({
      types: ["Species"],
      pk: "a",
    });
    expect(parseQuery({ types: "Nope" }).types).toEqual([]);
  });

  it("treats an empty help like a missing one", () => {
    expect(parseQuery({ help: "" }).help).toBeNull();
  });

  it("shows the tables for a view which is not the equations", () => {
    expect(parseQuery({ view: "nope" }).view).toBe("tables");
    expect(parseQuery({ view: "tables" }).view).toBe("tables");
  });

  it("writes only the non default values", () => {
    expect(
      toQuery({
        entry: null,
        model: null,
        pk: null,
        q: "",
        types: null,
        help: null,
        view: "tables",
      }),
    ).toEqual({});
    expect(
      toQuery({
        entry: "./m.xml",
        model: "m",
        pk: "p",
        q: "x",
        types: ["Species"],
        help: "types/Species",
        view: "equations",
      }),
    ).toEqual({
      entry: "./m.xml",
      model: "m",
      pk: "p",
      q: "x",
      types: "Species",
      help: "types/Species",
      view: "equations",
    });
  });

  it("round trips", () => {
    const state = {
      entry: "./a b.xml",
      model: "m",
      pk: "m/Species:s 1",
      q: "a&b",
      types: ["Species" as const],
      help: "types/Species",
      view: "equations" as const,
    };
    expect(parseQuery(toQuery(state) as Record<string, string>)).toEqual(state);
  });
});
