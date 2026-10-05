<script lang="ts">
/** Where the resolve of the resource of an annotation card stands. */
export type AnnotationCardState = "idle" | "loading" | "resolved" | "failed";
</script>

<script setup lang="ts">
import { computed, ref } from "vue";

import { annotationStructureUrl } from "@/api/client";
import HelpLabel from "@/components/help/HelpLabel.vue";
import ShowAllButton from "@/components/misc/ShowAllButton.vue";
import { conceptEntry } from "@/report/glossary";
import { isHttpUrl } from "@/report/text";
import type { AnnotationResource } from "@/types/annotation";

/** One resource of an annotation, shown the way cy3sbml shows it: the qualifier, the collection
 * and the identifier as badges, the term of the ontology with its synonyms, its description and
 * its cross references, the chemistry of a ChEBI compound or the protein of UniProt, and the
 * providers which show the entry. Before the resource is resolved, and when it cannot be, the card
 * keeps its head, so that the identifier is always a link. */
const props = defineProps<{
  resource: string;
  qualifier: string;
  info?: AnnotationResource | null;
  state: AnnotationCardState;
}>();

/** The synonyms shown before a "show all": a ChEBI compound has dozens of them. */
const SYNONYM_LIMIT = 5;

const allSynonyms = ref(false);
const structureFailed = ref(false);

const synonyms = computed(() => props.info?.ontology?.synonyms ?? []);
const shownSynonyms = computed(() =>
  allSynonyms.value ? synonyms.value : synonyms.value.slice(0, SYNONYM_LIMIT),
);
const xrefs = computed(() => props.info?.ontology?.xrefs ?? []);
const providers = computed(() => props.info?.providers ?? []);
const fallbackHref = computed(() =>
  isHttpUrl(props.resource)
    ? props.resource
    : `https://identifiers.org/${props.resource.replace(/^urn:miriam:/, "")}`,
);
const identifierHref = computed(() => props.info?.url ?? fallbackHref.value);
const messages = computed(() => [
  ...(props.info?.warnings ?? []),
  ...(props.info?.errors ?? []),
  ...(props.state === "failed" ? ["The resource could not be resolved."] : []),
]);

const chebiRows = computed(() => {
  const chebi = props.info?.chebi;
  if (!chebi) return [];
  return [
    { key: "chebiFormula", value: chebi.formula },
    { key: "chebiCharge", value: chebi.charge },
    { key: "chebiMass", value: chebi.mass },
  ].filter((row) => row.value !== null && row.value !== undefined);
});
const uniprotRows = computed(() => {
  const protein = props.info?.uniprot;
  if (!protein) return [];
  return [
    { key: "uniprotName", value: [protein.name, protein.entry].filter(Boolean).join(" ") },
    { key: "uniprotOrganism", value: protein.organism },
    { key: "uniprotGenes", value: (protein.genes ?? []).join(", ") },
    { key: "uniprotLength", value: protein.length },
    { key: "uniprotFunction", value: protein.function },
  ].filter((row) => row.value !== null && row.value !== undefined && row.value !== "");
});

function label(key: string): string {
  return conceptEntry(key)?.label ?? key;
}
function summary(key: string): string | undefined {
  return conceptEntry(key)?.summary;
}
</script>

<template>
  <div class="rounded-xl bg-gray-50 p-2.5 text-sm break-words" data-testid="annotation-card">
    <div class="flex flex-wrap items-baseline gap-1">
      <HelpLabel help-key="concepts/annotationQualifier" :tooltip="summary('annotationQualifier')">
        <span class="badge bg-[#13721c]" data-testid="annotation-qualifier">{{ qualifier }}</span>
      </HelpLabel>
      <a
        v-if="info?.collection"
        v-tooltip.bottom="summary('annotationCollection')"
        :href="info.collection.homepage ?? undefined"
        target="_blank"
        rel="noopener"
        class="badge bg-gray-900"
        data-testid="annotation-collection"
        >{{ info.collection.name ?? info.collection.prefix }}</a
      >
      <a
        v-tooltip.bottom="summary('annotationIdentifier')"
        :href="identifierHref"
        target="_blank"
        rel="noopener"
        class="badge bg-amber-600 font-mono !break-all !whitespace-normal"
        data-testid="annotation-identifier"
        >{{ info?.identifier ?? resource }}</a
      >
    </div>
    <p
      v-if="info?.patternMatch === false"
      class="mt-1 text-amber-700"
      data-testid="annotation-pattern-warning"
    >
      {{ info.identifier }} does not match the pattern of
      {{ info.collection?.name ?? info.collection?.prefix }}.
    </p>
    <p
      v-for="(message, i) in messages"
      :key="i"
      class="mt-1 text-amber-700"
      data-testid="annotation-warning"
    >
      {{ message }}
    </p>
    <p
      v-if="state === 'loading'"
      class="mt-1 text-xs text-gray-400"
      data-testid="annotation-loading"
    >
      resolving
    </p>

    <template v-if="info?.ontology">
      <div class="mt-1">
        <a
          v-if="info.ontology.ontology"
          v-tooltip.bottom="summary('annotationOntology')"
          :href="info.ontology.olsUrl ?? undefined"
          target="_blank"
          rel="noopener"
          class="badge bg-cyan-700"
          data-testid="annotation-ontology"
          >{{ info.ontology.ontology.toUpperCase() }}</a
        >
        <b class="ml-1" data-testid="annotation-label">{{ info.ontology.label }}</b>
        <a
          v-if="info.ontology.iri"
          :href="info.ontology.iri"
          target="_blank"
          rel="noopener"
          class="ml-1 text-xs break-all text-gray-500 hover:underline"
          data-testid="annotation-iri"
          >{{ info.ontology.iri }}</a
        >
      </div>
      <div v-if="synonyms.length" class="mt-1" data-testid="annotation-synonyms">
        <HelpLabel help-key="concepts/annotationSynonyms" :tooltip="summary('annotationSynonyms')">
          <span class="section-label">{{ label("annotationSynonyms") }}</span>
        </HelpLabel>
        <template v-for="(synonym, i) in shownSynonyms" :key="i">
          <span v-if="i > 0">; </span><span data-testid="annotation-synonym">{{ synonym }}</span>
        </template>
        <ShowAllButton
          v-if="!allSynonyms && synonyms.length > SYNONYM_LIMIT"
          :count="synonyms.length - SYNONYM_LIMIT"
          class="ml-1"
          @click="allSynonyms = true"
        />
      </div>
      <p
        v-if="info.ontology.description"
        class="mt-1 text-gray-800"
        data-testid="annotation-description"
      >
        {{ info.ontology.description }}
      </p>
    </template>

    <div
      v-if="info?.chebi"
      class="mt-2 flex flex-wrap items-start gap-3"
      data-testid="annotation-chebi"
    >
      <a
        v-if="info.chebi.structure && !structureFailed && info.identifier"
        :href="identifierHref"
        target="_blank"
        rel="noopener"
      >
        <img
          :src="annotationStructureUrl(info.identifier)"
          :alt="info.ontology?.label ?? info.identifier"
          class="max-w-full rounded border border-gray-200 bg-white"
          width="180"
          height="180"
          loading="lazy"
          data-testid="annotation-structure"
          @error="structureFailed = true"
        />
      </a>
      <table>
        <tbody>
          <tr v-for="row in chebiRows" :key="row.key">
            <td class="pr-3 text-gray-500">
              <HelpLabel :help-key="`concepts/${row.key}`" :tooltip="summary(row.key)">{{
                label(row.key)
              }}</HelpLabel>
            </td>
            <td class="font-mono">{{ row.value }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <table v-if="info?.uniprot" class="mt-1" data-testid="annotation-uniprot">
      <tbody>
        <tr v-for="row in uniprotRows" :key="row.key">
          <td class="pr-3 align-top text-gray-500">
            <HelpLabel :help-key="`concepts/${row.key}`" :tooltip="summary(row.key)">{{
              label(row.key)
            }}</HelpLabel>
          </td>
          <td>{{ row.value }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="xrefs.length" class="mt-1">
      <HelpLabel help-key="concepts/annotationXrefs" :tooltip="summary('annotationXrefs')">
        <span class="section-label">{{ label("annotationXrefs") }}</span>
      </HelpLabel>
      <!-- the test id sits on the links only: the HelpLabel is an anchor and stays outside -->
      <span data-testid="annotation-xrefs">
        <template v-for="xref in xrefs" :key="xref.label">
          <a
            v-if="xref.url"
            :href="xref.url"
            target="_blank"
            rel="noopener"
            class="mr-2 font-mono text-xs text-link hover:underline"
            >{{ xref.label }}</a
          >
          <span v-else class="mr-2 font-mono text-xs">{{ xref.label }}</span>
        </template>
      </span>
    </div>

    <div v-if="providers.length" class="mt-1 text-xs">
      <HelpLabel help-key="concepts/annotationProviders" :tooltip="summary('annotationProviders')">
        <span class="section-label">{{ label("annotationProviders") }}</span>
      </HelpLabel>
      <!-- the test id sits on the links only: the HelpLabel is an anchor and stays outside -->
      <span data-testid="annotation-providers">
        <template v-for="(provider, i) in providers" :key="provider.url">
          <span v-if="i > 0"> · </span>
          <a
            :href="provider.url"
            target="_blank"
            rel="noopener"
            class="text-link hover:underline"
            >{{ provider.name }}</a
          >
        </template>
      </span>
    </div>
  </div>
</template>

<style scoped>
@reference "@/assets/main.css";

.badge {
  @apply inline-block rounded-sm px-1.5 align-[1px] text-[11px] leading-[17px] whitespace-nowrap text-white;
}
.section-label {
  @apply mr-1 text-xs font-semibold tracking-wide text-gray-500 uppercase;
}
</style>
