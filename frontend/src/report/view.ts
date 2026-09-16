import { computed, type ComputedRef } from "vue";
import { useRoute, useRouter, type RouteLocationRaw } from "vue-router";

import type { ElementType } from "@/api/types";
import { parseQuery, toQuery, type ViewState } from "@/report/query";

type Mode = "push" | "replace";

/** The view state of the report page and the actions that write it back to the route. */
export function useReportView(): {
  state: ComputedRef<ViewState>;
  select(pk: string | null, mode?: Mode): Promise<unknown>;
  setSearch(q: string): Promise<unknown>;
  setTypes(types: ElementType[] | null): Promise<unknown>;
  setEntry(entry: string | null): Promise<unknown>;
  setModel(model: string | null): Promise<unknown>;
  routeFor(pk: string): RouteLocationRaw;
} {
  const route = useRoute();
  const router = useRouter();
  const state = computed(() => parseQuery(route.query));

  function update(patch: Partial<ViewState>, mode: Mode = "push"): Promise<unknown> {
    const query = { ...toQuery({ ...state.value, ...patch }) };
    // the url of a loaded report is not view state, keep it
    if (typeof route.query.url === "string") query.url = route.query.url;
    return router[mode]({ path: route.path, query });
  }

  return {
    state,
    select: (pk, mode = "push") => update({ pk }, mode),
    setSearch: (q) => update({ q }, "replace"),
    setTypes: (types) => update({ types }),
    setEntry: (entry) => update({ entry, model: null, pk: null }),
    setModel: (model) => update({ model, pk: null }),
    routeFor: (pk) => {
      const query = { ...toQuery({ ...state.value, pk }) };
      if (typeof route.query.url === "string") query.url = route.query.url;
      return { path: route.path, query };
    },
  };
}
