<script setup lang="ts">
import ElementLink from "@/components/misc/ElementLink.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import type { ElementRef } from "@/report/index";
import { useLimitedList } from "@/report/limitedList";

/** The elements of one edge kind group of `LinksColumn`, shown up to LIST_LIMIT at a time: a
 * compartment of Recon3D can link to more than ten thousand elements. */
const props = defineProps<{ refs: ElementRef[] }>();

const { shown, hiddenCount, showAll } = useLimitedList(() => props.refs);
</script>

<template>
  <dd>
    <div class="flex flex-wrap gap-1">
      <ElementLink
        v-for="element in shown"
        :key="`${element.entry ?? ''}#${element.pk}`"
        :pk="element.pk"
        :entry="element.entry"
        mark
        class="rounded border border-gray-200 bg-white px-1.5 py-0.5"
      />
    </div>
    <ShowAllButton v-if="hiddenCount > 0" :count="hiddenCount" class="mb-1" @click="showAll" />
  </dd>
</template>
