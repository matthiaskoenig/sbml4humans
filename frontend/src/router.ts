import { createRouter, createWebHistory } from "vue-router";

/** The router of the application. The unit tests mock this module (`tests/unit/setup.ts`): the
 * mock keeps the routes and gives each an eager page, and it builds a router of its own, so a
 * guard or another option added here does not run in the unit tests unless the mock carries it
 * too. */
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: () => import("@/pages/HomePage.vue") },
    { path: "/examples", name: "examples", component: () => import("@/pages/ExamplesPage.vue") },
    { path: "/examples/:id", name: "example", component: () => import("@/pages/ReportPage.vue") },
    { path: "/report", name: "report", component: () => import("@/pages/ReportPage.vue") },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});
