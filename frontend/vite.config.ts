import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

const root = fileURLToPath(new URL("./", import.meta.url));

/** The version the footer shows, the `version` of `package.json`, which follows the version of
 * the backend package. */
function version(): string {
  const manifest = JSON.parse(readFileSync(`${root}package.json`, "utf8")) as { version: string };
  return manifest.version;
}

/** The commit the footer links: the one the build passes in `VITE_COMMIT`, which the production
 * image takes as a build argument, otherwise the head of the repository. A build which has
 * neither, for example a container which copies the sources without the repository, leaves it
 * empty and the footer shows the version alone. */
function commit(): string {
  const passed = process.env.VITE_COMMIT?.trim();
  if (passed) return passed;
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], {
      cwd: root,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "";
  }
}

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  define: {
    __APP_VERSION__: JSON.stringify(version()),
    __APP_COMMIT__: JSON.stringify(commit()),
  },
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  build: {
    rolldownOptions: {
      output: {
        // KaTeX, which only the report page imports, is a chunk of its own: it changes with its
        // version alone, so a browser keeps it across releases, and the chunk of the report page
        // stays below the size vite warns about
        codeSplitting: { groups: [{ name: "katex", test: /node_modules[\\/]katex[\\/]/ }] },
      },
    },
  },
  server: { port: 3456, host: true, strictPort: true },
  preview: { port: 3456, host: true, strictPort: true },
});
