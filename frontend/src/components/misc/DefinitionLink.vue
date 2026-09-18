<script setup lang="ts">
import ValueText from "@/components/misc/ValueText.vue";
import { definitionLabel, isHttpUrl } from "@/report/text";

/** The definition url of a measure of an uncertainty: an entry of an ontology, a csymbol of
 * the distrib package or another definition of what the measure means (distrib §3.11.4). Only
 * an http(s) url is a link, every other string is shown as the text it is. The link shows the
 * local name of the term, which is what tells two parameters of one distribution apart, and
 * carries the whole url as its tooltip. */
defineProps<{ url: string | null | undefined }>();
</script>

<template>
  <a
    v-if="isHttpUrl(url)"
    v-tooltip.bottom.mono="url"
    :href="url!"
    target="_blank"
    rel="noopener"
    class="text-link hover:underline"
    data-testid="definition-link"
    >{{ definitionLabel(url!) }}</a
  >
  <ValueText v-else :value="url" />
</template>
