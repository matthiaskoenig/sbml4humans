/** The version of the application, the `version` of `frontend/package.json`, injected by the
 * `define` of `vite.config.ts`. */
export const APP_VERSION: string = __APP_VERSION__;

/** The commit the application was built from, injected by the `define` of `vite.config.ts` from
 * `VITE_COMMIT` or from the head of the repository. It is empty when the build knows neither,
 * for example in a container which copies the sources without the repository. */
export const APP_COMMIT: string = __APP_COMMIT__;
