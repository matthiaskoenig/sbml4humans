<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

import { readStorage, writeStorage } from "@/storage";

const props = withDefaults(
  defineProps<{
    direction: "horizontal" | "vertical";
    storageKey: string;
    initial: number;
    min?: number;
    collapsed?: boolean;
    sizedPane?: "first" | "second";
  }>(),
  { min: 120, collapsed: false, sizedPane: "first" },
);

const key = computed(() => `sbml4humans.split.${props.storageKey}`);
const size = ref(Number(readStorage(key.value)) || props.initial);
const container = ref<HTMLElement | null>(null);
const horizontal = computed(() => props.direction === "horizontal");

let dragging = false;

/** One arrow key press, in px. */
const STEP = 16;

function onPointerDown(event: PointerEvent): void {
  dragging = true;
  (event.target as HTMLElement).setPointerCapture(event.pointerId);
  document.body.style.cursor = horizontal.value ? "col-resize" : "row-resize";
  document.body.style.userSelect = "none";
}

function onPointerMove(event: PointerEvent): void {
  if (!dragging || !container.value) return;
  const rect = container.value.getBoundingClientRect();
  const fromStart = horizontal.value ? event.clientX - rect.left : event.clientY - rect.top;
  const total = horizontal.value ? rect.width : rect.height;
  const next = props.sizedPane === "first" ? fromStart : total - fromStart;
  size.value = Math.min(Math.max(next, props.min), total - props.min);
}

function onPointerUp(): void {
  if (!dragging) return;
  dragging = false;
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
  writeStorage(key.value, String(Math.round(size.value)));
}

onBeforeUnmount(onPointerUp);

/** The keyboard path of the separator: the arrow keys along the split move it by `STEP`, within
 * the same bounds as the drag, and remember the size like the end of a drag does. */
function onKeyDown(event: KeyboardEvent): void {
  const keys = horizontal.value ? ["ArrowLeft", "ArrowRight"] : ["ArrowUp", "ArrowDown"];
  const index = keys.indexOf(event.key);
  if (index < 0) return;
  event.preventDefault();
  // right and down move the separator towards the end, which grows the first pane
  const towardsEnd = index === 1;
  const delta = (towardsEnd ? STEP : -STEP) * (props.sizedPane === "first" ? 1 : -1);
  const rect = container.value?.getBoundingClientRect();
  const total = (horizontal.value ? rect?.width : rect?.height) ?? 0;
  // an unmeasured container (no layout yet) only keeps the lower bound
  const max = total > 0 ? Math.max(total - props.min, props.min) : Number.POSITIVE_INFINITY;
  size.value = Math.min(Math.max(size.value + delta, props.min), max);
  writeStorage(key.value, String(Math.round(size.value)));
}

const valueNow = computed(() => Math.round(size.value));

const sizedStyle = computed(() => ({
  flex: `0 0 ${size.value}px`,
  [horizontal.value ? "width" : "height"]: `${size.value}px`,
}));
</script>

<template>
  <div
    ref="container"
    class="flex min-h-0 min-w-0 flex-1"
    :class="horizontal ? 'flex-row' : 'flex-col'"
  >
    <div
      class="flex min-h-0 min-w-0 flex-col overflow-hidden"
      :class="sizedPane === 'first' ? '' : 'flex-1'"
      :style="sizedPane === 'first' ? sizedStyle : undefined"
    >
      <slot name="first" />
    </div>
    <template v-if="!collapsed">
      <div
        class="shrink-0 bg-gray-200 hover:bg-gray-400"
        :class="horizontal ? 'w-1 cursor-col-resize' : 'h-1 cursor-row-resize'"
        role="separator"
        tabindex="0"
        aria-label="resize the panes"
        :aria-orientation="horizontal ? 'vertical' : 'horizontal'"
        :aria-valuenow="valueNow"
        data-testid="split-handle"
        @keydown="onKeyDown"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      />
      <div
        class="flex min-h-0 min-w-0 flex-col overflow-hidden"
        :class="sizedPane === 'second' ? '' : 'flex-1'"
        :style="sizedPane === 'second' ? sizedStyle : undefined"
      >
        <slot name="second" />
      </div>
    </template>
  </div>
</template>
