import { defineConfig } from "@playwright/test";
const port = Number(process.env.NETWORK_TEST_PORT ?? 4174);
if (!Number.isInteger(port) || port < 1 || port > 65535)
  throw new Error("Invalid network test port.");
export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: "network.spec.ts",
  timeout: 60000,
  expect: { timeout: 10000 },
  workers: 1,
  maxFailures: 1,
  outputDir: "test-results/network",
  reporter: "list",
  use: {
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    baseURL: `http://127.0.0.1:${port}`,
    viewport: { width: 1600, height: 1000 },
    launchOptions: {
      args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    },
  },
  webServer: {
    command: `npm run build:network && node_modules/.bin/vite preview --mode e2e --outDir dist-network --host 127.0.0.1 --port ${port} --strictPort`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    timeout: 180000,
  },
});
