<script setup lang="ts">
import { ChevronRightIcon, ExternalLinkIcon, XIcon } from "@lucide/vue";
import { computed, defineAsyncComponent, nextTick, ref, watch, type Component } from "vue";

import type { SbmlType } from "@/api/types";
import HelpAttributes from "@/components/help/HelpAttributes.vue";
import HelpLink from "@/components/help/HelpLink.vue";
import HelpDescriptionText from "@/components/help/HelpDescriptionText.vue";
import HelpRules from "@/components/help/HelpRules.vue";
import HelpSection from "@/components/help/HelpSection.vue";
import HelpTechnical from "@/components/help/HelpTechnical.vue";
import { requiredWord } from "@/components/help/words";
import TypeMark from "@/components/misc/TypeMark.vue";
import { SBML_TYPES } from "@/data/sbmlTypes";
import { DOCS_URL, entryOfKey } from "@/report/glossary";
import {
  loadGlossaryDetails,
  type GlossaryDetails,
  type HelpEntry,
} from "@/report/glossaryDetails";
import { useReportView } from "@/report/view";

/** The explanation of one entry of the glossary, mounted once by the report page and shown for
 * the key of the route, `help=<key>`: a click on a label of the report opens it, every link
 * inside it opens another entry, and the back button of the browser walks back through them.
 * Nothing of what it says is written here: the label, the summary, the description, the technical
 * detail and the validation rules all come from the glossary, this component holds the words of
 * its own chrome and nothing else.
 *
 * It is a native `<dialog>` opened with `showModal()`, which gives the trap of the focus, Escape,
 * the page behind it made inert and the return of the focus to the label which opened it. */
const view = useReportView();

/** The long descriptions and the technical detail, the half megabyte of json which the first
 * dialog of a session fetches, not every page of the application. */
const details = ref<GlossaryDetails | null>(null);
/** The details could not be loaded, for example a reader who is offline with a report the local
 * server serves from a stale cache: the dialog then shows what it knows without them. */
const failed = ref(false);
let pending = false;

/** The import of the renderer of the descriptions, and with it `markdown-it`, the second half of
 * what a dialog costs and the other thing no page which shows no dialog should pay for. It is
 * started next to the details and shared with the async component below, so that the two halves
 * of a dialog are loaded at once instead of one after the other. */
let markdown: Promise<Component> | undefined;
function loadMarkdown(): Promise<Component> {
  if (!markdown) {
    markdown = import("@/components/help/HelpMarkdown.vue").then((module) => module.default);
    // the import is started before anything renders it, and a rejection which nothing waits for
    // yet is an unhandled one; the dialog answers it with the text of the description below
    markdown.catch(() => undefined);
  }
  return markdown;
}

/** The renderer, with the description as the text it is written in where its chunk cannot be
 * loaded: Vue keeps an async component which failed to load failed for the rest of the session,
 * so the alternative is an overview which is an empty heading. */
const HelpMarkdown = defineAsyncComponent({
  loader: loadMarkdown,
  errorComponent: HelpDescriptionText,
});

/** The key of the entry a type's attributes end with, the attributes every element carries. */
const SBASE_KEY = "types/SBase";

/** The words of the dialog itself: the headings of the parts of its body, the message of a body
 * without its details and the link of its footer. */
const HEADINGS = {
  overview: "Overview",
  technical: "Technical",
  rules: "Validation rules",
  attributes: "Attributes",
  related: "Related elements",
} as const;
const FAILED_MESSAGE = "The full explanation could not be loaded.";
const DOCS_LINK = "Open in the documentation";

const dialog = ref<HTMLDialogElement | null>(null);
const body = ref<HTMLElement | null>(null);
const title = ref<HTMLElement | null>(null);
/** The id `aria-labelledby` of the dialog names, so that the dialog is announced by its title. */
const TITLE_ID = "help-dialog-title";

const help = computed(() => view.state.value.help);

function loadDetails(): void {
  if (details.value || pending) return;
  pending = true;
  failed.value = false;
  void loadMarkdown();
  void loadGlossaryDetails().then(
    (loaded) => {
      details.value = loaded;
      pending = false;
    },
    () => {
      failed.value = true;
      pending = false;
    },
  );
}

/** The entry of a key. The key comes from the url and may be anything, so it is looked up with
 * `Object.hasOwn` rather than read off the object: `constructor` and `toString` are no entries of
 * the glossary, however much the object the json parsed into answers to them. */
function entryOf(loaded: GlossaryDetails, key: string): HelpEntry | null {
  return Object.hasOwn(loaded.entries, key) ? (loaded.entries[key] ?? null) : null;
}

const entry = computed(() => {
  const key = help.value;
  const loaded = details.value;
  return key && loaded ? entryOf(loaded, key) : null;
});

/** What the eager glossary of every page knows about the key, the label and the summary the
 * tooltips show, which head the dialog while the details are still loading. */
const eager = computed(() => (help.value ? entryOfKey(help.value) : undefined));

/** The last segment of the key, the name of the entry as the url writes it: the header of a
 * dialog whose entry the eager glossary does not carry either, a data type. */
const lastSegment = computed(() => {
  const key = help.value;
  return key ? key.slice(key.lastIndexOf("/") + 1) : "";
});

const heading = computed(() => entry.value?.label ?? eager.value?.label ?? lastSegment.value);
const summary = computed(() => entry.value?.summary ?? eager.value?.summary ?? "");
const loading = computed(() => !entry.value && !failed.value);

/** The type of a key which names one of the types of the report, so that the breadcrumb carries
 * the mark of the type as every other place of the report does. `SBase` and the entries of the
 * packages are types of the glossary without an element of their own and have no mark. */
function markOf(key: string | null | undefined): SbmlType | null {
  const segments = key?.split("/") ?? [];
  const type = segments.length === 2 && segments[0] === "types" ? segments[1]! : null;
  return type && Object.hasOwn(SBML_TYPES, type) ? (type as SbmlType) : null;
}

/** The mark of the entry itself, which a type has and an attribute, a link kind, a concept and a
 * data type have not; the mark of an attribute is the one of its owner, in front of it. */
const mark = computed(() => markOf(help.value));

/** The type an attribute belongs to, which stands in front of it in the breadcrumb. */
const owner = computed(() => {
  const key = entry.value?.owner;
  const loaded = details.value;
  const target = key && loaded ? entryOf(loaded, key) : null;
  return key && target ? { key, label: target.label, mark: markOf(key) } : null;
});

const hasTechnical = computed(() => {
  const current = entry.value;
  if (!current) return false;
  return (
    current.type !== undefined ||
    current.required !== undefined ||
    current.default !== undefined ||
    current.spec !== undefined
  );
});

/** The literals of an enumeration, which stand at the end of the overview and not in the
 * technical list: the description of such a data type ends by announcing them, "the two values
 * are:", and the list belongs to that sentence, as it does on the reference page. */
const values = computed(() => entry.value?.values ?? []);

/** The attributes of a type and, behind them, the common attributes of `SBase`, which every
 * element carries and no type repeats. The entry of `SBase` names and explains them itself. */
const attributeRows = computed(() => {
  const loaded = details.value;
  const current = entry.value;
  if (!loaded || !current?.attributes?.length) return [];
  const rows = current.attributes.flatMap((key) => {
    const target = entryOf(loaded, key);
    return target ? [{ key, entry: target }] : [];
  });
  const common = help.value === SBASE_KEY ? null : entryOf(loaded, SBASE_KEY);
  if (common) rows.push({ key: SBASE_KEY, entry: common });
  return rows;
});

const related = computed(() => {
  const loaded = details.value;
  if (!loaded) return [];
  return (entry.value?.related ?? []).flatMap((key) => {
    const target = entryOf(loaded, key);
    return target ? [{ key, label: target.label }] : [];
  });
});

/** The page of the entry on the documentation site, whose reference is generated from the same
 * glossary; without the details, which carry the page, the site itself. */
const docsHref = computed(() => `${DOCS_URL}${entry.value?.docs ?? ""}`);

/** The dialog follows the route: a key which arrives opens it, a key which leaves closes it and
 * a key which changes while it is open shows the new entry in place, without the dialog closing
 * and opening again, which would cost the reader the focus and the position of the page behind
 * it. The new entry starts at the top of the body and takes the focus with its title, so that a
 * reader who navigates with the keyboard or with a screen reader lands on what they opened. */
watch(
  help,
  async (key) => {
    if (!key) {
      if (dialog.value?.open) dialog.value.close();
      return;
    }
    loadDetails();
    // the details of a session which has shown a dialog already say at once that a key is no
    // entry: nothing opens for it, and the watcher below takes it out of the route. Only the
    // first dialog of a session has to open before it can know
    if (details.value && !entryOf(details.value, key)) return;
    await nextTick();
    const element = dialog.value;
    if (!element) return;
    if (!element.open) element.showModal();
    if (body.value) body.value.scrollTop = 0;
    title.value?.focus({ preventScroll: true });
  },
  { immediate: true },
);

/** A key which is no entry of the glossary: a link written by hand, an entry a later version
 * renamed, anything at all, since the key comes from the url. The key leaves the route, which
 * closes the dialog it opened, as the report closes the inspector of an element it does not
 * hold; it replaces the route rather than pushing one, so that the way back does not lead
 * through an entry which shows nothing. */
watch([details, help], ([loaded, key]) => {
  if (loaded && key && !entryOf(loaded, key)) void view.closeHelp("replace");
});

/** Escape closes a modal dialog itself and says so with `close`, so it is the route which has to
 * follow. A `close` the watcher above caused finds no key any more and does nothing. */
function onClose(): void {
  if (help.value) void view.closeHelp();
}

/** Where the button went down, which a click alone does not say: a click is delivered to the
 * common ancestor of the element the button went down on and the one it came up on, and for a
 * selection of the text of the dialog which ends on the backdrop that ancestor is the dialog
 * itself. Without this, selecting the summary and letting go outside the box would close the
 * dialog and lose the selection. */
let pressedOn: EventTarget | null = null;
function onMouseDown(event: MouseEvent): void {
  pressedOn = event.target;
}

/** A click which lands on the dialog element itself landed on the backdrop: everything inside it
 * is in the box the header, the body and the footer fill. Only a press which began there too
 * closes the dialog. */
function onClick(event: MouseEvent): void {
  const onBackdrop = event.target === dialog.value && pressedOn === dialog.value;
  // every click has had its press, so nothing is remembered beyond it: a click which arrives
  // without one, one a script dispatches, then finds nothing of an earlier press to pair with
  pressedOn = null;
  if (onBackdrop) void view.closeHelp();
}
</script>

<template>
  <dialog
    ref="dialog"
    class="m-auto w-[calc(100%-1.5rem)] max-w-2xl overflow-hidden rounded-lg bg-white p-0 shadow-xl backdrop:bg-gray-900/40"
    :aria-labelledby="TITLE_ID"
    data-testid="help-dialog"
    @close="onClose"
    @mousedown="onMouseDown"
    @click="onClick"
  >
    <div v-if="help" class="flex max-h-[80vh] flex-col">
      <!-- the header is one line: the breadcrumb gives way first, and where even it is too narrow
      for everything, on a telephone, the name of the type an attribute belongs to gives way to the
      name of the attribute and leaves its mark, which links it, the way the header of the
      inspector drops the name of an element before its type -->
      <!-- `relative`, because the name of the owner is hidden the way a screen reader still reads
      it where the header is narrow, which takes it out of the flow: a `<dialog>` is positioned by
      the browser, so without a containing block of its own every such element would be laid out
      against the dialog and add to what the dialog itself can scroll, and a dialog which scrolls
      carries this header out of sight -->
      <header
        class="@container relative flex h-12 shrink-0 items-center gap-2 border-b border-gray-200 px-4"
        data-testid="help-header"
      >
        <nav class="flex min-w-0 flex-1 items-center gap-1.5" data-testid="help-breadcrumb">
          <HelpLink
            v-if="owner"
            :help-key="owner.key"
            class="flex min-w-0 shrink items-center gap-1.5 text-sm text-link hover:underline"
            data-testid="help-owner"
          >
            <TypeMark v-if="owner.mark" :type="owner.mark" />
            <span class="sr-only truncate @sm:not-sr-only">{{ owner.label }}</span>
          </HelpLink>
          <ChevronRightIcon v-if="owner" class="size-3 shrink-0 text-gray-400" />
          <h2
            :id="TITLE_ID"
            ref="title"
            tabindex="-1"
            class="flex min-w-0 items-center gap-1.5 font-semibold focus:outline-none"
            data-testid="help-title"
          >
            <TypeMark v-if="!owner && mark" :type="mark" size="md" />
            <span class="truncate">{{ heading }}</span>
          </h2>
        </nav>
        <!-- the badge of the data type is the first thing to give way where the header is too
        narrow for everything, on a telephone: the name of a data type is long, the name of the
        entry is what a reader has to see, and the technical list of the body states the type
        again, two lines further down -->
        <HelpLink
          v-if="entry?.type"
          :help-key="entry.type.key"
          class="hidden shrink-0 rounded border border-gray-200 bg-gray-50 px-1.5 py-0.5 font-mono text-xs text-link hover:bg-gray-100 @sm:inline-block"
          data-testid="help-type-badge"
          >{{ entry.type.label }}</HelpLink
        >
        <span
          v-if="entry?.required !== undefined"
          class="shrink-0 rounded border border-gray-200 px-1.5 py-0.5 text-xs text-gray-600"
          data-testid="help-required-badge"
          >{{ requiredWord(entry.required) }}</span
        >
        <button
          type="button"
          class="shrink-0 rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-900"
          aria-label="close"
          data-testid="help-close"
          @click="view.closeHelp()"
        >
          <XIcon class="size-4" />
        </button>
      </header>
      <div
        ref="body"
        class="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-3"
        data-testid="help-body"
      >
        <!-- the lead of the dialog, the one sentence a tooltip of the report shows as well: the
        size of everything else of the dialog and a little more weight, so that it leads the
        explanation below it instead of reading as its caption -->
        <p v-if="summary" class="text-sm font-medium text-gray-900" data-testid="help-summary">
          {{ summary }}
        </p>
        <!-- the details are one fetch away, which is quick and is not nothing -->
        <div v-if="loading" class="mt-4 animate-pulse space-y-2" data-testid="help-skeleton">
          <div class="h-3 w-1/3 rounded bg-gray-100"></div>
          <div class="h-3 rounded bg-gray-100"></div>
          <div class="h-3 w-5/6 rounded bg-gray-100"></div>
        </div>
        <p v-else-if="!entry" class="mt-4 text-sm text-gray-500" data-testid="help-fallback">
          {{ FAILED_MESSAGE }}
        </p>
        <template v-else>
          <HelpSection
            v-if="entry.description || values.length"
            :title="HEADINGS.overview"
            data-testid="help-overview"
          >
            <HelpMarkdown
              v-if="entry.description"
              :markdown="entry.description"
              @navigate="view.openHelp"
            />
            <!-- the literals of an enumeration belong to the sentence which announces them, the
            last one of the description above -->
            <div
              v-if="values.length"
              class="flex flex-wrap gap-1"
              :class="{ 'mt-3': entry.description }"
              data-testid="help-values"
            >
              <code
                v-for="value in values"
                :key="value"
                class="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs text-gray-800"
                >{{ value }}</code
              >
            </div>
          </HelpSection>
          <HelpSection v-if="hasTechnical" :title="HEADINGS.technical" data-testid="help-technical">
            <HelpTechnical :entry="entry" />
          </HelpSection>
          <HelpSection v-if="entry.rules?.length" :title="HEADINGS.rules" data-testid="help-rules">
            <HelpRules :rules="entry.rules" />
          </HelpSection>
          <HelpSection
            v-if="attributeRows.length"
            :title="HEADINGS.attributes"
            data-testid="help-attributes"
          >
            <HelpAttributes :rows="attributeRows" />
          </HelpSection>
          <HelpSection v-if="related.length" :title="HEADINGS.related" data-testid="help-related">
            <div class="flex flex-wrap gap-1.5">
              <HelpLink
                v-for="item in related"
                :key="item.key"
                :help-key="item.key"
                class="rounded border border-gray-200 bg-white px-2 py-0.5 text-sm text-link hover:bg-gray-50"
                >{{ item.label }}</HelpLink
              >
            </div>
          </HelpSection>
        </template>
      </div>
      <footer class="shrink-0 border-t border-gray-200 px-4 py-2 text-xs">
        <a
          :href="docsHref"
          target="_blank"
          rel="noopener"
          class="inline-flex items-center gap-1 text-link hover:underline"
          data-testid="help-docs-link"
          >{{ DOCS_LINK }}<ExternalLinkIcon class="size-3"
        /></a>
      </footer>
    </div>
  </dialog>
</template>
