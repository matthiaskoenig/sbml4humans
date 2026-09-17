import { computed, ref, watch, type ComputedRef } from "vue";

/** Every list in the inspector shows at most this many items before a "show all" button appears. */
export const LIST_LIMIT = 50;

export interface LimitedList<T> {
  /** The items to render: the first LIST_LIMIT until `showAll` is called, all of them after. */
  shown: ComputedRef<T[]>;
  /** The number of items `shown` currently leaves out. */
  hiddenCount: ComputedRef<number>;
  /** Reveal the rest of the list. */
  showAll: () => void;
}

/** The first LIST_LIMIT items of a reactive list, the count of the rest, and an action that
 * reveals them. The expansion resets whenever the list itself changes, so a component instance
 * the inspector reuses for another element of the same type never carries a previous "show all"
 * over to a list it was never clicked for. */
export function useLimitedList<T>(items: () => T[]): LimitedList<T> {
  const list = computed(items);
  const expanded = ref(false);
  watch(list, () => {
    expanded.value = false;
  });
  const shown = computed(() => (expanded.value ? list.value : list.value.slice(0, LIST_LIMIT)));
  const hiddenCount = computed(() => Math.max(0, list.value.length - LIST_LIMIT));
  return { shown, hiddenCount, showAll: () => (expanded.value = true) };
}
