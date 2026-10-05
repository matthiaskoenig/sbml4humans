import { fileURLToPath, URL } from "node:url";

import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config.ts";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      include: ["tests/unit/**/*.test.ts"],
      setupFiles: ["tests/unit/setup.ts"],
      // the tests render in jsdom and are CPU bound: half the cores leave the machine room for
      // the rest of what runs on it, a backend or an end to end run, instead of competing for it
      maxWorkers: "50%",
      // a backstop for a machine under load: no test waits on time of its own (fake timers, no
      // lazy page imports, see tests/unit/setup.ts), the default of 5 s is CPU time alone
      testTimeout: 15_000,
      root: fileURLToPath(new URL("./", import.meta.url)),
    },
  }),
);
