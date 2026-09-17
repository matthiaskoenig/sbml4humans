<script setup lang="ts">
import { ref } from "vue";

const emit = defineEmits<{ submit: [file: File] }>();
const dragging = ref(false);
const input = ref<HTMLInputElement | null>(null);

function pick(files: FileList | null | undefined): void {
  const file = files?.[0];
  if (file) emit("submit", file);
}

function onDrop(event: DragEvent): void {
  dragging.value = false;
  pick(event.dataTransfer?.files);
}
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center"
    :class="dragging ? 'border-link bg-blue-50' : 'border-gray-300'"
    data-testid="file-dropzone"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <i class="pi pi-upload text-2xl text-gray-400" />
    <p class="text-sm text-gray-600">Drop an SBML file or a COMBINE archive here, or</p>
    <button
      type="button"
      class="rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
      @click="input?.click()"
    >
      Choose a file
    </button>
    <input
      ref="input"
      type="file"
      class="hidden"
      accept=".xml,.sbml,.gz,.omex,.zip"
      data-testid="file-input"
      @change="pick(($event.target as HTMLInputElement).files)"
    />
  </div>
</template>
