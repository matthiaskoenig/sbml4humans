# Input

A qualitative species a transition reads, with the sign of its influence.

An input names the [qualitative species](qualitativespecies.md) whose level a [transition](transition.md) reads. Together with the [outputs](output.md) of the transitions the inputs are the influence graph of the model, the picture a reader of a regulatory model actually wants: who acts on whom, and whether the action activates or inhibits.

It is an element of the report and not a row of its transition, because the specification derives it from `SBase`: it may carry an identifier, a name, an SBO term, notes and annotations, and the reference to its species starts here, not at the transition around it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [qualitativeSpecies](#qualitativespecies) | `SIdRef` | - | the species whose level the transition reads | [qual 3.6.1](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [thresholdLevel](#thresholdlevel) | `integer` | - | the level of the species at which the input acts | [qual 3.6.1](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [transitionEffect](#transitioneffect) | `transitionInputEffect` | - | whether the transition consumes the level of the species it reads | [qual 3.6.1](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [sign](#sign) | `sign` | - | whether the influence of the species activates or inhibits | [qual 3.6.1](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="qualitativespecies"></span>**qualitativeSpecies**

The attribute is required and names a [qualitative species](qualitativespecies.md) of the model. The report links it, and the inspector of that species shows the input under "referenced by", which is how the transitions that read an entity are found.

<span id="thresholdlevel"></span>**thresholdLevel**

A multi valued species does not act the same way at every level: it acts on one target above one level and on another above a higher one. The threshold level is that level, and the identifier of the input stands for it in the math of a [function term](functionterm.md), so that a condition reads `A >= theta_B_A` instead of a bare number.

The report shows the threshold in the column "threshold" of the inputs of a transition and in the inspector.

<span id="transitioneffect"></span>**transitionEffect**

The effect is `none`, where the transition only reads the level, which is what a logical model does, or `consumption`, where the firing of the transition takes the level away from the species, which is what a Petri net does with the tokens of the places before a transition. The attribute is required.

The report shows the effect in the table of the inputs in the inspector of the transition.

<span id="sign"></span>**sign**

The sign is `positive` for an activation, `negative` for an inhibition, `dual` where the species does both depending on the level of the others, and `unknown` where the file does not say. The specification adds it for visualisation: the mathematics of the model is in the [function terms](functionterm.md), and the sign is what lets a reader, or a drawing of the influence graph, see an arrow and a bar without reading the conditions.

The report shows the sign next to the species of the input in the column "inputs" of the transitions and in the table of the inputs in the inspector.

## Related elements

- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [QualitativeSpecies](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Output](output.md): a qualitative species a transition changes, with the effect it has on it
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.6.1 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
