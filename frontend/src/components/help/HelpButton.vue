<script setup lang="ts">
import { CircleHelpIcon } from "@lucide/vue";
import { computed } from "vue";

import HelpLink from "@/components/help/HelpLink.vue";
import { explainName } from "@/components/help/words";

/** The help of a place whose words are taken: the header of a column of an element table, which
 * sorts it, and the heading of a section, which is not a label a reader would click. The icon
 * stands next to them and opens the entry, and the click stops there, so that the control it
 * stands next to neither sorts nor selects.
 *
 * It is the same link as a `HelpLabel`, and since it shows no words of its own it carries a name
 * for a reader who does not see it. */
const props = defineProps<{ helpKey: string; label: string }>();

const name = computed(() => explainName(props.label));
</script>

<template>
  <HelpLink
    :help-key="helpKey"
    :aria-label="name"
    class="inline-flex shrink-0 rounded-sm text-gray-400 hover:text-link focus-visible:outline-2 focus-visible:outline-link"
    data-testid="help-button"
    @click.stop
  >
    <CircleHelpIcon class="size-3.5" />
  </HelpLink>
</template>
