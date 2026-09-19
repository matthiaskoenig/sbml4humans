<script setup lang="ts">
import type { EdgeKind, FluxObjective, UserDefinedConstraintComponent } from "@/api/types";
import ElementLink from "@/components/misc/ElementLink.vue";
import ValueText from "@/components/misc/ValueText.vue";
import { useReportIndex } from "@/report/context";

/** The terms of a sum of fbc as the sum they are: the flux objectives of an objective, which
 * the objective maximises or minimises, and the components of a user defined constraint, which
 * its bounds keep between them. A term is its coefficient times a variable, `C × J`, and a
 * quadratic term is the square of the variable, `C × J²`, or the product with a second one,
 * `C × J × J2` (fbc Version 3 §3.7 and §3.8). */
defineProps<{ terms: (FluxObjective | UserDefinedConstraintComponent)[] }>();
const index = useReportIndex();

const PLUS = " + ";
const TIMES = " × ";

interface Factor {
  kind: EdgeKind;
  id: string | null | undefined;
}

/** The variable of a term and its second variable, with the edge of the term which names each:
 * the reactions of a flux objective, the reactions or parameters of a component. */
function factors(term: FluxObjective | UserDefinedConstraintComponent): [Factor, Factor] {
  // the reaction is required of a flux objective, so it tells the two types apart
  if ("reaction" in term) {
    return [
      { kind: "fluxObjective", id: term.reaction },
      { kind: "reaction2", id: term.reaction2 },
    ];
  }
  return [
    { kind: "variable", id: term.variable },
    { kind: "variable2", id: term.variable2 },
  ];
}

/** The coefficient of a component names a parameter, the one of a flux objective is a number. */
function coefficientId(term: FluxObjective | UserDefinedConstraintComponent): string | null {
  return "reaction" in term ? null : (term.coefficient ?? null);
}

function coefficientValue(
  term: FluxObjective | UserDefinedConstraintComponent,
): FluxObjective["coefficient"] | null {
  return "reaction" in term ? term.coefficient : null;
}

function resolve(pk: string, kind: EdgeKind, id: string | null | undefined): string | null {
  return index.value?.resolve(pk, kind, id) ?? null;
}

/** A quadratic term without a second variable is the square of its variable. */
function squared(term: FluxObjective | UserDefinedConstraintComponent): boolean {
  return term.variableType === "quadratic" && !factors(term)[1].id;
}
</script>

<template>
  <ValueText v-if="!terms.length" :value="null" />
  <!-- the separators are text of their own, so that the cell reads as the formula it is -->
  <span v-else data-testid="terms">
    <template v-for="(term, i) in terms" :key="term.pk">
      <span v-if="i > 0" class="text-gray-500">{{ PLUS }}</span>
      <ElementLink
        v-if="coefficientId(term)"
        :pk="resolve(term.pk, 'coefficient', coefficientId(term))"
        :label="coefficientId(term)"
      />
      <ValueText v-else :value="coefficientValue(term)" />
      <span class="text-gray-500">{{ TIMES }}</span>
      <ElementLink
        :pk="resolve(term.pk, factors(term)[0].kind, factors(term)[0].id)"
        :label="factors(term)[0].id"
      />
      <sup v-if="squared(term)">2</sup>
      <template v-if="factors(term)[1].id">
        <span class="text-gray-500">{{ TIMES }}</span>
        <ElementLink
          :pk="resolve(term.pk, factors(term)[1].kind, factors(term)[1].id)"
          :label="factors(term)[1].id"
        />
      </template>
    </template>
  </span>
</template>
