import { set, type createGtag } from "vue-gtag";
import type { RouteLocationNormalizedGeneric, Router } from "vue-router";

/** vue-gtag does not export its settings type, so it is recovered from `createGtag`, the
 * function every caller passes it to. */
type GtagSettings = Parameters<typeof createGtag>[0];

/** The Google Analytics measurement id sbml4humans reports to. */
const TAG_ID = "G-TZ6E25RS0Q";

/** Whether a build reports page views: the production build of sbml4humans.de does, a
 * development server does not, and neither does the build which ships with the python package
 * (`npm run build:package`, `VITE_ANALYTICS=off`), which serves the models of one machine to
 * that machine. */
export function analyticsEnabled(env: { PROD: boolean; VITE_ANALYTICS?: string }): boolean {
  return env.PROD && env.VITE_ANALYTICS !== "off";
}

/** The origin and path of a route, without its query or hash: a report page carries the loaded
 * model's url, the search term and the permalink id in the query, and none of that belongs in
 * an analytics report. */
function locationOf(path: string): string {
  return window.location.origin + path;
}

/**
 * Builds the vue-gtag settings for the given router. The page tracker's template, the initial
 * `config` call and the `router:track:before` hook all report `page_location` and `page_path`
 * built from the route's path alone, so the query of a report page (the model `url`, the search
 * `q`, the permalink `pk`) never reaches Google Analytics. The hook additionally calls vue-gtag's
 * `set` before the page view of a route is sent, so the events gtag.js fires on its own after a
 * navigation (for example the automatic engagement events) also carry the stripped location.
 */
export function gtagSettings(router: Router): GtagSettings {
  return {
    tagId: TAG_ID,
    pageTracker: {
      router,
      template: (route: RouteLocationNormalizedGeneric) => ({
        page_path: route.path,
        page_title: route.name?.toString(),
        page_location: locationOf(route.path),
      }),
    },
    config: {
      page_location: locationOf(window.location.pathname),
    },
    hooks: {
      "router:track:before": (route: RouteLocationNormalizedGeneric) => {
        set({ page_location: locationOf(route.path) });
      },
    },
  };
}
