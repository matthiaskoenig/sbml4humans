# Output

A qualitative species a transition changes, with the effect it has on it.

An output names the [qualitative species](qualitativespecies.md) whose level a [transition](transition.md) changes. Its [transition effect](output.md#transitioneffect) is what tells the two formalisms of the package apart: `assignmentLevel` for a logical model, `production` for a Petri net.

It is an element of the report and not a row of its transition, because the specification derives it from `SBase`: it may carry an identifier, a name, an SBO term, notes and annotations, and the reference to its species starts here, not at the transition around it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [qualitativeSpecies](#qualitativespecies) | [`SIdRef`](datatypes.md#sidref) | - | the species whose level the transition changes | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [outputLevel](#outputlevel) | [`integer`](datatypes.md#integer) | - | the level the transition produces per result level | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [transitionEffect](#transitioneffect) | `transitionOutputEffect` | - | whether the transition sets the level of the species or adds to it | [qual 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="qualitativespecies"></span>**qualitativeSpecies**

The attribute is required and names a [qualitative species](qualitativespecies.md) of the model which is not constant, since a constant species is an input of the system which no transition may change. The report links it, and the inspector of that species shows the output under "referenced by", which is how the transitions that decide the level of an entity are found.

<span id="outputlevel"></span>**outputLevel**

Where the transition effect is `production`, the level the species gains is the result level of the term which fires multiplied by the output level, which is the weight of the arc of a Petri net. The attribute is required there and has no meaning for an `assignmentLevel` output, where the level is the result level itself.

The report shows the output level in the table of the outputs in the inspector of the transition.

<span id="transitioneffect"></span>**transitionEffect**

The effect is `assignmentLevel`, where the level of the species becomes the result level of the term which fires, which is how a logical model is written, or `production`, where the result level multiplied by the output level is added to it, which is how a Petri net is written. The attribute is required, and it is the attribute which says in which of the two formalisms a file is written.

The report shows the effect in the table of the outputs in the inspector of the transition.

## Related elements

- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [QualitativeSpecies](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Input](input.md): a qualitative species a transition reads, with the sign of its influence
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.6.2 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
