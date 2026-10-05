import { defineConfig, devices } from "@playwright/test";

/** The port of the production build the tests run against (`vite preview`), apart from the port
 * 3456 of the development server, which may run next to the tests. */
const PORT = 4173;
const CHROME = { ...devices["Desktop Chrome"], viewport: { width: 1600, height: 1000 } };
/** The phone of the narrow layout, which `mobile.spec.ts` alone is written for. */
const PHONE = devices["Pixel 7"];

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  // a report is built by the one backend of the tests and rendered by a browser per worker, both
  // CPU bound: half the cores leave the machine room for the backend and for itself
  workers: "50%",
  // the backend builds the report of every example the specs open before they run
  globalSetup: "./tests/e2e/globalSetup.ts",
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "retain-on-failure",
  },
  // a production build, which serves every page at once: the development server transforms the
  // modules of a page on the first request for them, which the parallel workers wait for. The
  // build is made afresh for every run, so that no earlier build is tested.
  webServer: {
    command: `npm run build:e2e && npx vite preview --mode e2e --outDir dist-e2e --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: false,
    timeout: 180_000,
  },
  projects: [
    {
      name: "chromium",
      testIgnore: /examples-walk|mobile/,
      use: CHROME,
    },
    {
      name: "mobile",
      testMatch: /mobile/,
      use: PHONE,
    },
    // the walk over every example runs alone, after the other specs: creating a report is CPU
    // bound in the backend, which the parallel workers of the other specs would compete for
    {
      name: "examples-walk",
      testMatch: /examples-walk/,
      dependencies: ["chromium"],
      use: CHROME,
    },
  ],
});
