import { computed, ref, watch, type ComputedRef } from "vue";

/** Every list in the inspector shows at most this many items before a "show all" button appears. */
export const LIST_LIMIT = 50;

export interface LimitedList<T> {
  /** The items to render: the first LIST_LIMIT until `showAll` is called, all of them after. */
  shown: ComputedRef<T[]>;
  /** The number of items `shown` currently leaves out: 0 once `showAll` is called. */
  hiddenCount: ComputedRef<number>;
  /** Reveal the rest of the list. */
  showAll: () => void;
}

/** The first `limit` items of a reactive list, the count of the rest, and an action that
 * reveals them. The expansion resets whenever the list itself changes, so a component instance
 * the inspector reuses for another element of the same type never carries a previous "show all"
 * over to a list it was never clicked for.
 *
 * `limit` is LIST_LIMIT for a flat list. A list which nests, the branches of a gene product
 * association, passes a smaller one, because every one of its items opens a list of its own. */
export function useLimitedList<T>(items: () => T[], limit: number = LIST_LIMIT): LimitedList<T> {
  const list = computed(items);
  const expanded = ref(false);
  watch(list, () => {
    expanded.value = false;
  });
  const shown = computed(() => (expanded.value ? list.value : list.value.slice(0, limit)));
  const hiddenCount = computed(() => (expanded.value ? 0 : Math.max(0, list.value.length - limit)));
  return {
    shown,
    hiddenCount,
    showAll: () => (expanded.value = true),
  };
}
