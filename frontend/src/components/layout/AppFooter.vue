<script setup lang="ts">
import { computed } from "vue";

import { APP_COMMIT, APP_VERSION } from "@/build";
import { DOCS_URL } from "@/report/glossary";

/** The report page is a full height workspace and puts the footer under its split, where the
 * padding which lifts the footer off the content of a scrolling page would take height from the
 * tables and the inspector. The dense footer carries the same text in the same order. */
const props = withDefaults(defineProps<{ dense?: boolean }>(), { dense: false });

const REPOSITORY_URL = "https://github.com/matthiaskoenig/sbml4humans";

/** The concept DOI of the archive on Zenodo, which always resolves to the newest release. */
const DOI_URL = "https://doi.org/10.5281/zenodo.22827237";

const PRIVACY_URL = `${REPOSITORY_URL}/blob/main/frontend/privacy_notice.md`;

/** The commit in the short form git itself prints. */
const shortCommit = computed(() => APP_COMMIT.slice(0, 7));
const commitUrl = computed(() => `${REPOSITORY_URL}/commit/${APP_COMMIT}`);
</script>

<template>
  <!-- `mt-auto` puts the footer at the bottom of a short page, the padding keeps it clear of the
       content of a page which fills the window, e.g. the grid of the examples; the dense footer
       of the report page sits right under the split, which has taken the height it needs -->
  <footer
    class="text-xs text-gray-500"
    :class="props.dense ? 'shrink-0 bg-white px-4' : 'mt-auto pt-8'"
    data-testid="app-footer"
  >
    <div class="border-t border-gray-200" :class="props.dense ? 'py-2' : 'pt-6'">
      <p>
        SBML4Humans {{ APP_VERSION
        }}<template v-if="APP_COMMIT">
          (<a :href="commitUrl" class="text-link hover:underline" data-testid="footer-commit">{{
            shortCommit
          }}</a
          >)</template
        >
        is developed on
        <a :href="REPOSITORY_URL" class="text-link hover:underline" data-testid="footer-github"
          >GitHub</a
        >
        (MIT) in the
        <a
          href="https://livermetabolism.com"
          class="text-link hover:underline"
          data-testid="footer-lab"
          >lab of Matthias König</a
        >. If you use it in your work, cite
        <a :href="DOI_URL" class="text-link hover:underline" data-testid="footer-doi"
          >the Zenodo DOI</a
        >, the
        <a :href="DOCS_URL" class="text-link hover:underline" data-testid="footer-docs"
          >documentation</a
        >
        shows
        <a
          :href="`${DOCS_URL}#how-to-cite`"
          class="text-link hover:underline"
          data-testid="footer-cite"
          >how to cite</a
        >
        it. Funded by
        <a href="https://summerofcode.withgoogle.com/" class="text-link hover:underline"
          >Google Summer of Code 2021</a
        >
        and the German Research Foundation (DFG).
        <a :href="PRIVACY_URL" class="text-link hover:underline" data-testid="footer-privacy"
          >Privacy notice</a
        >.
      </p>
      <p class="mt-1">&copy; 2021-2026 Matthias König</p>
    </div>
  </footer>
</template>
