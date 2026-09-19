# KineticLaw

The formula which gives the speed of a reaction.

The kinetic law of a reaction holds the formula which computes how fast the process runs, and the local parameters which only that formula uses. The formula may use the global elements of the model, its own local parameters and the species which the reaction declares as reactants, products or modifiers. Its units are the extent units of the model divided by its time units.

The report shows the rendered formula, the units it derives for it and the table of the local parameters.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [math](#math) | `Math` | the rate formula of the reaction | [core 4.11.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfLocalParameters](#listoflocalparameters) | `list` | the parameters which only this kinetic law uses | [core 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math is an expression which returns a number, the rate of change of the extent of the reaction. A kinetic law without a formula leaves the speed of the reaction undefined.

The report renders the formula in the column "kinetic law" of the reactions and in the inspector.

<span id="listoflocalparameters"></span>**listOfLocalParameters**

The list holds the [local parameters](localparameter.md) of the kinetic law. A local parameter hides a global parameter of the same identifier inside the formula, which is worth knowing when a value looks surprising.

The report shows the local parameters as a table in the inspector of the kinetic law and of the reaction.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | `latex` | the units of the rate formula as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the formula from the units of the quantities it uses. They should be the extent units of the model divided by its time units, which is the check a modeller wants to make on a rate law.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [LocalParameter](localparameter.md): a named value which only one kinetic law uses
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
