import type { LocationQuery, LocationQueryRaw, LocationQueryValue } from "vue-router";

import { isOdeFormat, type OdeFormat } from "@/api/client";
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
  /** Key of the glossary entry the help dialog shows, null = dialog closed. */
  help: string | null;
  /** What the report page shows next to the inspector: the element tables or the
   * differential equations of the model. */
  view: ReportViewKind;
  /** The format of sbmlode whose code the equations show, null = the math. */
  code: OdeFormat | null;
}

/** The views of the report page. */
export type ReportViewKind = "tables" | "equations";

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
    help: first(query.help),
    view: first(query.view) === "equations" ? "equations" : "tables",
    code: isOdeFormat(first(query.code) ?? "") ? (first(query.code) as OdeFormat) : null,
  };
}

export function toQuery(state: ViewState): LocationQueryRaw {
  const query: LocationQueryRaw = {};
  if (state.entry) query.entry = state.entry;
  if (state.model) query.model = state.model;
  if (state.pk) query.pk = state.pk;
  if (state.q) query.q = state.q;
  if (state.types !== null) query.types = state.types.join(",");
  if (state.help) query.help = state.help;
  if (state.view === "equations") query.view = state.view;
  // the code is a tab of the equations
  if (state.view === "equations" && state.code) query.code = state.code;
  return query;
}
