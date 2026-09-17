import { beforeEach, describe, expect, it, vi } from "vitest";
import { set } from "vue-gtag";
import type * as vueGtag from "vue-gtag";
import type { RouteLocationNormalizedGeneric, Router } from "vue-router";

import { gtagSettings } from "@/analytics";

vi.mock("vue-gtag", async (importOriginal) => {
  const original = await importOriginal<typeof vueGtag>();
  return { ...original, set: vi.fn() };
});

/** The query a report page carries: a private model url with a token and a search term. */
const QUERY = "?url=https%3A%2F%2Fprivate.example%2Fmodel.xml%3Ftoken%3Dsecret&q=abc";

/** A route carrying the query of a report page. `route.path` itself never contains the query
 * (vue-router keeps the query in `route.query` and `route.fullPath`), which is exactly why
 * building the reported location from `route.path` keeps it out. */
function buildRoute(): RouteLocationNormalizedGeneric {
  return {
    path: "/report",
    fullPath: `/report${QUERY}`,
    query: { url: "https://private.example/model.xml?token=secret", q: "abc" },
    hash: "#frag",
    name: "report",
    params: {},
    matched: [],
    meta: {},
    redirectedFrom: undefined,
  } as unknown as RouteLocationNormalizedGeneric;
}

describe("gtagSettings", () => {
  beforeEach(() => {
    // the page the settings are built on carries the query and a hash too, so a location built
    // from `window.location.href` differs from the expected one
    window.history.replaceState({}, "", `/report${QUERY}#frag`);
    vi.mocked(set).mockClear();
  });

  it("builds a template whose page_location and page_path carry no query", () => {
    const settings = gtagSettings({} as Router);
    const template = settings.pageTracker?.template;
    if (typeof template !== "function") throw new Error("expected a template function");
    const result = template(buildRoute());
    if (!result || !("page_path" in result)) throw new Error("expected a Pageview result");
    expect(result.page_path).toBe("/report");
    expect(result.page_location).toBe(`${window.location.origin}/report`);
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
    const location = (settings.config as { page_location?: string } | undefined)?.page_location;
    expect(location).toBe(`${window.location.origin}/report`);
  });

  it("the router:track:before hook calls vue-gtag's set with a page_location without query", () => {
    const settings = gtagSettings({} as Router);
    const hook = settings.hooks?.["router:track:before"];
    if (!hook) throw new Error("expected a router:track:before hook");
    hook(buildRoute());
    expect(set).toHaveBeenCalledTimes(1);
    expect(set).toHaveBeenCalledWith({ page_location: `${window.location.origin}/report` });
  });
});
