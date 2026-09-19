<script setup lang="ts">
import type { Constraint } from "@/api/types";
import AttributeRow from "@/components/inspector/AttributeRow.vue";
import MathView from "@/components/misc/MathView.vue";
import XhtmlView from "@/components/misc/XhtmlView.vue";

defineProps<{ element: Constraint }>();
</script>

<template>
  <AttributeRow :type="element.sbmlType" field="math"
    ><MathView :math="element.math" display
  /></AttributeRow>
  <!-- the message is XHTML written for the reader of a simulation, under the rules of the
  notes (core §4.10.2), so it is rendered and not printed as markup -->
  <AttributeRow :type="element.sbmlType" field="message" wide
    ><XhtmlView :xhtml="element.message" testid="message"
  /></AttributeRow>
</template>
