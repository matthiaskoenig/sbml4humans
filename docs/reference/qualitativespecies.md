# Qualitative species

An entity of a qualitative model, which carries a level instead of an amount.

A qualitative species is what a [species](species.md) is to a kinetic model: the thing the model is about. Its state is not a concentration but a level, a whole number between zero and its [maximum level](qualitativespecies.md#max-level), which stands for a range of activity, for example "the gene is off" and "the gene is on".

It is the node of the influence graph of a logical model and the place of a Petri net. Which of the two a file writes is read from the [transitions](transition.md) which change it.

The report shows the qualitative species of a model in a section of their own, with their levels, and links every transition which reads or changes one in its inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [compartment](#compartment) | `SIdRef` | the compartment the qualitative species is located in | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [constant](#constant) | `boolean` | whether no transition may change the level of the species | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [initial level](#initial-level) | `integer` | the level of the species at the start of a simulation | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [max level](#max-level) | `integer` | the highest level the species can take | [qual 3.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="compartment"></span>**compartment**

The attribute is required and names a [compartment](compartment.md) of the model, the same way a [species](species.md) names one. The compartment of a qualitative model carries no size which enters a formula; it says where in the cell the entity is, which is what tells two copies of one protein in two compartments apart.

The report links the compartment in the column "compartment" and in the inspector.

<span id="constant"></span>**constant**

A constant qualitative species is an input of the system: transitions read it and none of them is allowed to change it, so its level is a condition of the experiment and not a result of the model. The attribute is required.

The report shows the flag as a mark in the column "constant" and in the inspector.

<span id="initial-level"></span>**initial level**

The initial level is the state the entity starts in, a whole number which cannot be negative and cannot exceed the maximum level. It is optional: a model which is analysed over all of its states, which is what an attractor analysis of a logical model does, gives no starting state.

The report shows the level in the column "initial level" and in the inspector, and an unset level as a dash.

<span id="max-level"></span>**max level**

The maximum level decides how the whole model is read: with the value one the entity is Boolean, off or on, and every condition over it is a logical one; with a higher value it is multi valued and its levels stand for the thresholds at which it acts differently on the things it regulates.

It is optional, because the levels a species actually takes can be derived from the [result levels](functionterm.md#result-level) of the transitions which change it.

The report shows the level in the column "max level" and in the inspector.

## Related elements

- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Output](output.md): a qualitative species a transition changes, with the effect it has on it
- [Compartment](compartment.md): a bounded space in which species are located
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.5 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
