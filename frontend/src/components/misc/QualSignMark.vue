<script setup lang="ts">
import { computed } from "vue";

// The sign of an input says whether the species it names activates or inhibits the transition
// (qual §3.6.1). It is what turns the inputs and outputs of a model into a picture of
// activation and inhibition, so it is shown as the glyph a drawing of an influence graph uses
// and the word of the specification is one hover away.
const props = defineProps<{ sign: string | null | undefined }>();

const GLYPHS: Readonly<Record<string, string>> = {
  positive: "+",
  negative: "−",
  dual: "±",
  unknown: "?",
};

const glyph = computed(() => (props.sign ? (GLYPHS[props.sign] ?? props.sign) : null));
const color = computed(() => {
  if (props.sign === "positive") return "text-emerald-700";
  if (props.sign === "negative") return "text-rose-700";
  return "text-gray-500";
});
</script>

<template>
  <span
    v-if="glyph"
    v-tooltip.bottom="sign"
    class="font-mono font-semibold"
    :class="color"
    data-testid="qual-sign"
    >{{ glyph }}</span
  >
  <span v-else class="text-gray-400">-</span>
</template>
