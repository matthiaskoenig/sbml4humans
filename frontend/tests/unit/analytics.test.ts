import { describe, expect, it, vi } from "vitest";
import { set } from "vue-gtag";
import type * as vueGtag from "vue-gtag";
import type { Router } from "vue-router";
import type { RouteLocationNormalizedGeneric } from "vue-router";

import { gtagSettings } from "@/analytics";

vi.mock("vue-gtag", async (importOriginal) => {
  const original = await importOriginal<typeof vueGtag>();
  return { ...original, set: vi.fn() };
});

/** A route carrying the query a report page uses: a private model url with a token, a search
 * term and a permalink id. `route.path` itself never contains the query (vue-router keeps the
 * query in `route.query` and `route.fullPath`), which is exactly why building the reported
 * location from `route.path` keeps it out. */
function buildRoute(): RouteLocationNormalizedGeneric {
  return {
    path: "/report",
    fullPath: "/report?url=https%3A%2F%2Fprivate.example%2Fmodel.xml%3Ftoken%3Dsecret&q=abc",
    query: { url: "https://private.example/model.xml?token=secret", q: "abc" },
    hash: "",
    name: "report",
    params: {},
    matched: [],
    meta: {},
    redirectedFrom: undefined,
  } as unknown as RouteLocationNormalizedGeneric;
}

describe("gtagSettings", () => {
  it("builds a template whose page_location and page_path carry no query", () => {
    const settings = gtagSettings({} as Router);
    const route = buildRoute();
    const template = settings.pageTracker?.template;
    if (typeof template !== "function") throw new Error("expected a template function");
    const result = template(route);
    if (!result || !("page_path" in result)) throw new Error("expected a Pageview result");
    expect(result.page_path).toBe("/report");
    expect(result.page_path).not.toContain("?");
    expect(result.page_location).not.toContain("?");
    expect(result.page_location).not.toContain("token");
    expect(result.page_location).not.toContain("private.example");
  });

  it("sets page_title from the route name", () => {
    const settings = gtagSettings({} as Router);
    const template = settings.pageTracker?.template;
    if (typeof template !== "function") throw new Error("expected a template function");
    const result = template(buildRoute());
    if (!result || !("page_path" in result)) throw new Error("expected a Pageview result");
    expect(result.page_title).toBe("report");
  });

  it("builds a config with a page_location that carries no query", () => {
    const settings = gtagSettings({} as Router);
    expect(settings.config).toBeDefined();
    const location = (settings.config as { page_location?: string }).page_location;
    expect(location).not.toContain("?");
  });

  it("the router:track:before hook calls vue-gtag's set with a page_location without query", () => {
    const settings = gtagSettings({} as Router);
    const hook = settings.hooks?.["router:track:before"];
    if (!hook) throw new Error("expected a router:track:before hook");
    hook(buildRoute());
    expect(set).toHaveBeenCalledTimes(1);
    const call = vi.mocked(set).mock.calls[0];
    if (!call) throw new Error("expected set to have been called");
    const config = call[0];
    const location = (config as { page_location?: string }).page_location;
    expect(location).toBeDefined();
    expect(location).not.toContain("?");
    expect(location).not.toContain("token");
    expect(location).not.toContain("private.example");
  });
});
