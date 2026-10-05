import { inject, type InjectionKey, ref, type Ref } from "vue";

import type { ApiError } from "@/api/client";
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

/** The failure of the validation of the report, provided by the report page: null while it is
 * pending, once it is done and where no page provides it. The inspector of the document shows it
 * with its details, which the chip of the app bar has no room for. */
export const ValidationFailureKey: InjectionKey<Ref<ApiError | null>> = Symbol("ValidationFailure");

export function useValidationFailure(): Ref<ApiError | null> {
  return inject(ValidationFailureKey, () => ref(null), true);
}
