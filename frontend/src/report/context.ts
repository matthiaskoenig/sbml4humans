import { inject, type InjectionKey, type Ref } from "vue";

import type { ReportIndex } from "@/report/index";
import type { ValidationIndex } from "@/report/validationIndex";

/** The index of the current archive entry, provided by the report page. */
export const ReportIndexKey: InjectionKey<Ref<ReportIndex | null>> = Symbol("ReportIndex");

export function useReportIndex(): Ref<ReportIndex | null> {
  const index = inject(ReportIndexKey);
  if (!index) throw new Error("useReportIndex() outside of the report page");
  return index;
}

/** The validation of the current archive entry, provided by the report page: null while it is
 * pending and after it failed. */
export const ValidationIndexKey: InjectionKey<Ref<ValidationIndex | null>> =
  Symbol("ValidationIndex");

export function useValidationIndex(): Ref<ValidationIndex | null> {
  const index = inject(ValidationIndexKey);
  if (!index) throw new Error("useValidationIndex() outside of the report page");
  return index;
}
