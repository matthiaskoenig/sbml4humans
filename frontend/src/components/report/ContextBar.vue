<script setup lang="ts">
import { computed } from "vue";

import type { Model } from "@/api/types";
import SelectInput from "@/components/input/SelectInput.vue";
import type { ReportIndex } from "@/report/index";
import { useReportView } from "@/report/view";

const props = defineProps<{ index: ReportIndex; entries: string[]; entry: string; model: Model }>();
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
const packages = computed(
  () => props.index.document.packages?.map((pkg) => pkg.prefix).filter((p) => p) ?? [],
);
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
    <span v-else class="truncate font-mono text-gray-700" data-testid="model-name">{{
      model.id
    }}</span>
    <span class="whitespace-nowrap text-gray-500" data-testid="document-info">
      L{{ index.document.level }}V{{ index.document.version }}
      <span
        v-for="pkg in packages"
        :key="pkg"
        class="ml-1 rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-700"
        >{{ pkg }}</span
      >
    </span>
  </div>
</template>
