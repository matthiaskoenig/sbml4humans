import { inject, type InjectionKey, type Ref } from "vue";

import type { ReportIndex } from "@/report/index";

/** The index of the current archive entry, provided by the report page. */
export const ReportIndexKey: InjectionKey<Ref<ReportIndex | null>> = Symbol("ReportIndex");

export function useReportIndex(): Ref<ReportIndex | null> {
  const index = inject(ReportIndexKey);
  if (!index) throw new Error("useReportIndex() outside of the report page");
  return index;
}
