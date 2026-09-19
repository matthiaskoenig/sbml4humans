<script setup lang="ts">
import HelpLink from "@/components/help/HelpLink.vue";

/** A label of the report which opens the explanation of what it names: the label of an attribute
 * row of the inspector, the type in the header of the inspector, the heading of a group of links
 * and the header of a column of a nested table. It is the same real link as every link inside the
 * dialog, so that a reader can open the entry in a new tab or copy it, and it keeps the hover
 * tooltip the label carried before, the one sentence of the glossary.
 *
 * It inherits the font, the size and the colour of the label it replaces and says what it does
 * with the cursor and a dotted underline, which sets it apart from a link which navigates. A key
 * the glossary does not have leaves the plain text the label was: nothing of the report is
 * clickable which leads nowhere. */
defineProps<{
  /** The entry the label opens, `undefined` where the glossary has none. */
  helpKey?: string;
  /** The sentence of the hover tooltip, which the label showed before it was clickable. */
  tooltip?: string;
}>();
</script>

<template>
  <!-- the link is inline and as wide as its text: a label which its column truncates is clipped
  by that column, so the ellipsis stays and exactly the visible label is the hit area -->
  <HelpLink
    v-if="helpKey"
    v-tooltip.bottom="tooltip"
    :help-key="helpKey"
    class="cursor-help decoration-dotted underline-offset-2 hover:underline focus-visible:underline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-link"
    data-testid="help-label"
    ><slot
  /></HelpLink>
  <span v-else v-tooltip.bottom="tooltip"><slot /></span>
</template>
