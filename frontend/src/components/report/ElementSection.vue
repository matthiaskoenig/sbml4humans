<script setup lang="ts">
import type { SbmlElement, ElementType } from "@/api/types";
import TypeMark from "@/components/misc/TypeMark.vue";
import ElementTable from "@/components/report/ElementTable.vue";
import { typeInfo } from "@/data/sbmlTypes";

defineProps<{ type: ElementType; rows: SbmlElement[]; total: number }>();
</script>

<template>
  <section :id="`section-${type}`" class="scroll-mt-2" :data-testid="`section-${type}`">
    <h2 class="flex items-center gap-2 px-1 pt-4 pb-2 text-sm font-semibold text-gray-800">
      <TypeMark :type="type" size="md" />
      {{ typeInfo(type).plural }}
      <span class="font-mono text-xs font-normal text-gray-500" data-testid="section-count">
        {{ rows.length === total ? total : `${rows.length} / ${total}` }}
      </span>
    </h2>
    <div class="overflow-hidden rounded border border-gray-200">
      <ElementTable :type="type" :rows="rows" />
    </div>
  </section>
</template>
