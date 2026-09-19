<script setup lang="ts">
/** The description of an entry as the text of the glossary, which the dialog shows in place of
 * the rendered markdown when the chunk of the renderer cannot be loaded: a reader who lost the
 * network after the report, or a page of a deployment which the file it asks for no longer has.
 * Vue keeps an async component which failed to load failed, so without this the overview of
 * every dialog of that session would be an empty heading. The markup of the markdown stays as it
 * is written, the words are what the reader came for; the lines are kept, so that the paragraphs
 * of a description stay paragraphs. */
defineProps<{ markdown: string }>();
</script>

<template>
  <div class="text-sm leading-relaxed whitespace-pre-line" data-testid="help-description-text">
    {{ markdown }}
  </div>
</template>
