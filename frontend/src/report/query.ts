import type { LocationQuery, LocationQueryRaw, LocationQueryValue } from "vue-router";

import type { ElementType } from "@/api/types";
import { isElementType } from "@/data/sbmlTypes";

/** The view state of the report page, kept in the route query. */
export interface ViewState {
  /** Manifest location of the SBML entry, null = master or first entry. */
  entry: string | null;
  /** Id of the model or model definition, null = main model. */
  model: string | null;
  /** Selected element, null = inspector closed. */
  pk: string | null;
  /** Search text. */
  q: string;
  /** Visible element types, null = all. */
  types: ElementType[] | null;
}

function first(value: LocationQueryValue | LocationQueryValue[] | undefined): string | null {
  const single = Array.isArray(value) ? value[0] : value;
  return single ? single : null;
}

export function parseQuery(query: LocationQuery): ViewState {
  const types = first(query.types);
  return {
    entry: first(query.entry),
    model: first(query.model),
    pk: first(query.pk),
    q: first(query.q) ?? "",
    types: types === null ? null : types.split(",").filter(isElementType),
  };
}

export function toQuery(state: ViewState): LocationQueryRaw {
  const query: LocationQueryRaw = {};
  if (state.entry) query.entry = state.entry;
  if (state.model) query.model = state.model;
  if (state.pk) query.pk = state.pk;
  if (state.q) query.q = state.q;
  if (state.types !== null) query.types = state.types.join(",");
  return query;
}
