import type { Math, Transition } from "@/api/types";

/** One row of the transition table of a transition. */
export interface TransitionTerm {
  pk: string;
  math: Math | null | undefined;
  resultLevel: number | null | undefined;
  /** The default term has no condition: it holds wherever no function term does. */
  isDefault: boolean;
}

/** What the condition of the default term reads, in the inspector and in the element table. */
export const OTHERWISE = "otherwise";

/** The transition table of a transition (qual §3.6.6): the function terms in the order in which
 * they are read, the first one whose condition holds deciding the level, and the default term as
 * the last row, which holds wherever none of them does. */
export function transitionTerms(transition: Transition): TransitionTerm[] {
  const rows: TransitionTerm[] = (transition.listOfFunctionTerms ?? []).map((term) => ({
    pk: term.pk,
    math: term.math,
    resultLevel: term.resultLevel,
    isDefault: false,
  }));
  const fallback = transition.defaultTerm;
  if (fallback) {
    rows.push({
      pk: fallback.pk,
      math: null,
      resultLevel: fallback.resultLevel,
      isDefault: true,
    });
  }
  return rows;
}
