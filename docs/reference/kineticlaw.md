# Kinetic law

The formula which gives the speed of a reaction.

The kinetic law of a reaction holds the formula which computes how fast the process runs, and the local parameters which only that formula uses. The formula may use the global elements of the model, its own local parameters and the species which the reaction declares as reactants, products or modifiers. Its units are the extent units of the model divided by its time units.

The report shows the rendered formula, the units it derives for it and the table of the local parameters.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| math | `Math` | <span id="math"></span>the rate formula of the reaction | [Section 4.11.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| local parameters | `list` | <span id="local-parameters"></span>the parameters which only this kinetic law uses | [Section 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| derived units | `latex` | <span id="derived-units"></span>the units of the rate formula as the report derives them |

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Local parameter](localparameter.md): a named value which only one kinetic law uses
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
