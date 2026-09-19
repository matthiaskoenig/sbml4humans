import { computed, type ComputedRef } from "vue";
import { useRoute, useRouter, type LocationQueryRaw, type RouteLocationRaw } from "vue-router";

import type { ElementType } from "@/api/types";
import { parseQuery, toQuery, type ViewState } from "@/report/query";

type Mode = "push" | "replace";

/** The keys of the route query which say where the report came from, the url of a model and the
 * token of a local report: they are not view state, and every route of the report keeps them. */
const SOURCE_KEYS = ["url", "local"] as const;

/** The view state of the report page and the actions that write it back to the route. */
export function useReportView(): {
  state: ComputedRef<ViewState>;
  select(pk: string | null, mode?: Mode): Promise<unknown>;
  setSearch(q: string): Promise<unknown>;
  setTypes(types: ElementType[] | null): Promise<unknown>;
  setEntry(entry: string | null): Promise<unknown>;
  setModel(model: string | null): Promise<unknown>;
  routeFor(pk: string, across?: { entry: string; model: string | null }): RouteLocationRaw;
} {
  const route = useRoute();
  const router = useRouter();
  const state = computed(() => parseQuery(route.query));

  /** The query of a view state, with the source of the report the route names. */
  function queryOf(next: ViewState): LocationQueryRaw {
    const query = { ...toQuery(next) };
    for (const key of SOURCE_KEYS) {
      const value = route.query[key];
      if (typeof value === "string") query[key] = value;
    }
    return query;
  }

  function update(patch: Partial<ViewState>, mode: Mode = "push"): Promise<unknown> {
    return router[mode]({ path: route.path, query: queryOf({ ...state.value, ...patch }) });
  }

  return {
    state,
    select: (pk, mode = "push") => update({ pk }, mode),
    setSearch: (q) => update({ q }, "replace"),
    setTypes: (types) => update({ types }),
    setEntry: (entry) => update({ entry, model: null, pk: null }),
    setModel: (model) => update({ model, pk: null }),
    // an element of another entry is shown in the report of that entry and in its model, and
    // neither the search nor the type filter of this entry says anything about that one
    routeFor: (pk, across) => {
      const next = across
        ? { entry: across.entry, model: across.model, pk, q: "", types: null }
        : { ...state.value, pk };
      return { path: route.path, query: queryOf(next) };
    },
  };
}
