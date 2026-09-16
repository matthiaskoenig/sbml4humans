import { createRouter, createWebHistory } from "vue-router";

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
