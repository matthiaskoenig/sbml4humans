<script setup lang="ts">
import { computed } from "vue";

import type { ApiError } from "@/api/client";
import type { Model } from "@/api/types";
import SelectInput from "@/components/input/SelectInput.vue";
import ValidationSummary from "@/components/report/ValidationSummary.vue";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";
import type { ValidationState } from "@/stores/report";

const props = defineProps<{
  index: ReportIndex;
  entries: string[];
  entry: string;
  model: Model;
  validationState: ValidationState | null;
  validationError: ApiError | null;
}>();
const view = useReportView();

const entryOptions = computed(() =>
  props.entries.map((location) => ({ label: location, value: location })),
);
const modelOptions = computed(() =>
  props.index.models.map((model) => ({
    label: `${model.id ?? model.pk}${model.kind === "modelDefinition" ? " (definition)" : ""}`,
    value: model.id ?? "",
  })),
);
const packages = computed(() => props.index.document.packages?.map((pkg) => pkg.prefix) ?? []);
</script>

<template>
  <div class="flex min-w-0 items-center gap-3 text-sm">
    <!-- an archive of several entries picks the one to report, the single entry of a plain SBML
    file is a name the backend gives it and the reader never chose, so it is not shown -->
    <SelectInput
      v-if="entries.length > 1"
      :model-value="entry"
      :options="entryOptions"
      aria-label="archive entry"
      data-testid="entry-select"
      @update:model-value="(value: string) => view.setEntry(value)"
    />
    <SelectInput
      v-if="index.models.length > 1"
      :model-value="model.id ?? ''"
      :options="modelOptions"
      aria-label="model"
      data-testid="model-select"
      @update:model-value="(value: string) => view.setModel(value)"
    />
    <!-- a narrow window leaves the name to the type bar, which carries it as well -->
    <span v-else class="truncate font-mono text-gray-700 max-md:hidden" data-testid="model-name">{{
      model.id
    }}</span>
    <!-- a phone leaves the level, the version and the packages to the inspector of the document,
    the row has no room for them next to the selects -->
    <span class="whitespace-nowrap text-gray-500 max-sm:hidden" data-testid="document-info">
      L{{ index.document.level }}V{{ index.document.version }}
      <span
        v-for="pkg in packages"
        :key="pkg"
        class="ml-1 rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-700"
        >{{ pkg }}</span
      >
    </span>
    <ValidationSummary :index="index" :state="validationState" :error="validationError" />
  </div>
</template>
