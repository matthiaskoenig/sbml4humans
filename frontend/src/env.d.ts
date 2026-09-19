/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  /** "off" keeps vue-gtag out of a production build, see `analyticsEnabled`. */
  readonly VITE_ANALYTICS?: string;
}

/** The constants the `define` of `vite.config.ts` injects, see `src/build.ts`. */
declare const __APP_VERSION__: string;
declare const __APP_COMMIT__: string;
