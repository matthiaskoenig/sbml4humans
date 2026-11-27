import { config } from "@vue/test-utils";
import { vi } from "vitest";
import { defineComponent } from "vue";
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import type * as Router from "@/router";

// Parents can render without their app shell. Tooltip behavior tests register the real directive.
config.global.directives.tooltip = {};

/** The page of every route of the router of the unit tests. */
const Page = defineComponent({ name: "TestPage", render: () => null });

// The routes of the router load their pages lazily, and the first navigation of a test file
// waits for that import: the transform of the report page and of everything it imports would
// count against the timeout of whichever test navigates first, which a loaded machine exceeds.
// The tests mount the components they test themselves, so the router of the tests keeps the
// routes and gives each an eager page that renders nothing; a test which renders the pages
// through the router (`smoke.test.ts`) calls `vi.unmock("@/router")`.
vi.mock("@/router", async (importOriginal) => {
  const { router } = await importOriginal<typeof Router>();
  const routes = router.options.routes.map((route) =>
    "component" in route && route.component ? { ...route, component: Page } : route,
  ) as RouteRecordRaw[];
  return { router: createRouter({ history: createWebHistory(), routes }) };
});
