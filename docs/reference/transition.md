# Transition

What the level of a qualitative species becomes, and under which condition.

A transition is to a qualitative model what a [reaction](reaction.md) with its kinetic law is to a kinetic one: it holds the dynamics. It reads the [qualitative species](qualitativespecies.md) of its [inputs](input.md), it changes those of its [outputs](output.md), and its [function terms](functionterm.md) say which level the outputs take: the result level of the first term whose condition holds, and the level of the [default term](defaultterm.md) where none of them holds.

Its identifier is optional and has no mathematical meaning, because nothing in a qualitative model refers to a transition.

The report shows the transitions of a model in a section of their own, with the species they read and the species they change, and the inspector shows the function terms as the table of condition and result level they are.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [inputs](#inputs) | `list` | the qualitative species the transition reads | [qual 3.6.1](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [outputs](#outputs) | `list` | the qualitative species the transition changes | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [function terms](#function-terms) | `list` | the terms which decide the level, in the order in which they are read | [qual 3.6.3](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [default term](#default-term) | `DefaultTerm` | the term which holds in every state no function term covers | [qual 3.6.4](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="inputs"></span>**inputs**

Every [input](input.md) names one [qualitative species](qualitativespecies.md) whose level the condition of a function term may read, with the threshold at which it matters and the sign of its influence. A transition may list none of them, in which case its terms read no species at all.

The report shows the species of the inputs with their sign in the column "inputs" and the table of the inputs in the inspector.

<span id="outputs"></span>**outputs**

Every [output](output.md) names one [qualitative species](qualitativespecies.md) whose level the transition sets or increases. A transition without outputs changes nothing, which is why a model which does something has at least one.

The report shows the species of the outputs in the column "outputs" and the table of the outputs in the inspector.

<span id="function-terms"></span>**function terms**

The list is the transition table of the transition. Its [terms](functionterm.md) are read in the order in which the file writes them and the first one whose condition holds decides the result level, so two terms whose conditions overlap are not a contradiction: the earlier one wins.

The report shows the terms as a table of condition and result level in the inspector of the transition, with the default term as its last row.

<span id="default-term"></span>**default term**

Every transition has exactly one [default term](defaultterm.md), which makes the transition table total: whatever the levels of the inputs, some term gives a result level.

The report shows it as the last row of the table of the function terms, under the condition "otherwise".

## Related elements

- [Qualitative species](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Output](output.md): a qualitative species a transition changes, with the effect it has on it
- [Function term](functionterm.md): one row of the transition table: a condition and the level it results in
- [Default term](defaultterm.md): the level of a transition in every state no function term covers
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.6 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
