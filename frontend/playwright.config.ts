import { defineConfig, devices } from "@playwright/test";

const PORT = 3456;
const CHROME = { ...devices["Desktop Chrome"], viewport: { width: 1600, height: 1000 } };
/** The phone of the narrow layout, which `mobile.spec.ts` alone is written for. */
const PHONE = devices["Pixel 7"];

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev",
    url: `http://localhost:${PORT}`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
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
