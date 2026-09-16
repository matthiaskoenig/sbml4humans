<script setup lang="ts">
import type { ModelHistory } from "@/api/types";

defineProps<{ history: ModelHistory | null | undefined }>();

function name(creator: { givenName?: string | null; familyName?: string | null }): string {
  return [creator.givenName, creator.familyName].filter((part) => part).join(" ") || "unknown";
}
</script>

<template>
  <p v-if="!history" class="text-gray-400">-</p>
  <div v-else class="flex flex-col gap-1 text-sm" data-testid="history">
    <p v-for="(creator, i) in history.creators" :key="i">
      {{ name(creator)
      }}<span v-if="creator.organization" class="text-gray-500">, {{ creator.organization }}</span>
      <a
        v-if="creator.email"
        :href="`mailto:${creator.email}`"
        class="ml-1 text-link hover:underline"
        >{{ creator.email }}</a
      >
    </p>
    <p v-if="history.createdDate" class="text-xs text-gray-500">
      created {{ history.createdDate }}
    </p>
    <p v-for="date in history.modifiedDates" :key="date" class="text-xs text-gray-500">
      modified {{ date }}
    </p>
  </div>
</template>
