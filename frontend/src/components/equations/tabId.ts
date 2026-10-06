import type { OdeFormat } from "@/api/client";

/** The id of the element of a tab of the equations, `null` the math, which labels the panel the
 * tab shows (`aria-labelledby`). */
export function tabId(code: OdeFormat | null): string {
  return `equations-tab-${code ?? "math"}`;
}
