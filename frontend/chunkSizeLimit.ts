import type { Plugin } from "vite";

/** The size above which a chunk of the build fails it [kB, as vite counts them: thousands of
 * characters of the minified code]. vite only warns above its `build.chunkSizeWarningLimit`, a
 * warning nobody reads in a green build: the report page grew past it once unnoticed, before
 * KaTeX became a chunk of its own. */
export const CHUNK_SIZE_LIMIT = 500;

/** The size of a chunk in kB, as vite's report of a build counts it. */
export function chunkSize(code: string): number {
  return code.length / 1000;
}

/** A plugin which fails the build when a JavaScript chunk is larger than `limit` kB, naming every
 * such chunk and its size. */
export function chunkSizeLimit(limit: number = CHUNK_SIZE_LIMIT): Plugin {
  return {
    name: "sbml4humans:chunk-size-limit",
    apply: "build",
    generateBundle(_options, bundle) {
      const large = Object.values(bundle)
        .filter((output) => output.type === "chunk" && chunkSize(output.code) > limit)
        .map((output) =>
          output.type === "chunk"
            ? `${output.fileName} (${chunkSize(output.code).toFixed(1)} kB)`
            : output.fileName,
        );
      if (large.length > 0) {
        this.error(
          `chunks larger than ${limit} kB: ${large.join(", ")}; split them, see the codeSplitting of vite.config.ts`,
        );
      }
    },
  };
}
