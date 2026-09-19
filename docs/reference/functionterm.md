# FunctionTerm

One row of the transition table: a condition and the level it results in.

A function term is a condition and a level. The condition is ordinary MathML which returns a boolean value and reads the levels of the [qualitative species](qualitativespecies.md) of the transition; where it holds, the [outputs](output.md) take the result level of the term.

The terms of a [transition](transition.md) are read in order and the first one which holds decides, so the list of terms with the [default term](defaultterm.md) behind it is the state transition table of the transition.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [resultLevel](#resultlevel) | `integer` | the level the outputs take where the condition of the term holds | [qual 3.6.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |
| [math](#math) | `Math` | the condition under which the term decides the level | [qual 3.6.5](https://sbml.org/documents/specifications/level-3/version-1/qual/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="resultlevel"></span>**resultLevel**

The result level is a whole number which cannot be negative. An `assignmentLevel` output takes it as its new level, a `production` output gains it multiplied by its output level. The attribute is required.

The report shows it in the column "result level" of the table of the terms in the inspector of the transition.

<span id="math"></span>**math**

The math is an expression which returns a boolean value, usually a comparison of the level of a species with the threshold of an input combined with `and`, `or` and `not`. A symbol in it is the identifier of a qualitative species, which means its level, of an [input](input.md), which means its threshold level, or of an [output](output.md), which means its output level.

The report renders the condition in the table of the terms in the inspector of the transition and links every element the condition reads.

## Related elements

- [Transition](transition.md): what the level of a qualitative species becomes, and under which condition
- [DefaultTerm](defaultterm.md): the level of a transition in every state no function term covers
- [QualitativeSpecies](qualitativespecies.md): an entity of a qualitative model, which carries a level instead of an amount
- [Qualitative Models (qual)](qual.md): the package which describes a model whose entities carry a level

## Specification

[SBML Level 3 Package: Qualitative Models, Version 1 Release 1](https://sbml.org/documents/specifications/level-3/version-1/qual/), Section 3.6.5 (Chaouiya et al. 2013, BMC Syst Biol 7:135).
