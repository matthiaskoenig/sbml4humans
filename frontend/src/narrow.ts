import { readonly, ref, type Ref } from "vue";

/** The one breakpoint of the application, the `md` of Tailwind: a window below it is narrow, a
 * phone, and the styles say so with the `md:` variants. What is not a style, which panes the
 * report page has and whether it opens with the model selected, asks `useNarrow`. */
export const NARROW_QUERY = "(max-width: 767.98px)";

let narrow: Ref<boolean> | null = null;

/** Whether the window is narrow, followed for as long as the application runs: one listener for
 * every caller. An environment without `matchMedia` is wide. */
export function useNarrow(): Readonly<Ref<boolean>> {
  if (narrow === null) {
    const state = ref(false);
    if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
      const media = window.matchMedia(NARROW_QUERY);
      state.value = media.matches;
      media.addEventListener("change", (event) => (state.value = event.matches));
    }
    narrow = state;
  }
  return readonly(narrow);
}
