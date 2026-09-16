<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

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
const size = ref(Number(localStorage.getItem(key.value)) || props.initial);
const container = ref<HTMLElement | null>(null);
const horizontal = computed(() => props.direction === "horizontal");

let dragging = false;

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
  localStorage.setItem(key.value, String(Math.round(size.value)));
}

onBeforeUnmount(onPointerUp);

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
        data-testid="split-handle"
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
