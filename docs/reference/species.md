# Species

A pool of a chemical entity in a compartment.

A species is a pool of entities which the model treats as indistinguishable: a metabolite, a protein, an ion, a gene. It is located in exactly one [compartment](compartment.md), it may participate in reactions, and its quantity is what most simulations compute. The quantity is an amount or a concentration, depending on the attribute "only substance units".

The report shows the initial quantity of a species, its units, the flags which say how it may change, and links its compartment and every reaction it takes part in.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| compartment | `SIdRef` | <span id="compartment"></span>the compartment the species is located in | [Section 4.6.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| initial amount | `double` | <span id="initial-amount"></span>the amount of the species when the simulation starts | [Section 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| initial concentration | `double` | <span id="initial-concentration"></span>the concentration of the species when the simulation starts | [Section 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| substance units | `UnitSIdRef` | <span id="substance-units"></span>the units of the amount of the species | [Section 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| only substance units | `boolean` | <span id="only-substance-units"></span>whether the identifier of the species stands for an amount instead of a concentration | [Section 4.6.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| boundary condition | `boolean` | <span id="boundary-condition"></span>whether the quantity of the species is left unchanged by the reactions | [Section 4.6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| constant | `boolean` | <span id="constant"></span>whether the quantity of the species stays fixed during a simulation | [Section 4.6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| conversion factor | `SIdRef` | <span id="conversion-factor"></span>the parameter which converts the extent of a reaction into the quantity of the species | [Section 4.6.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| fbc | `SpeciesFbc` | <span id="fbc"></span>the chemical formula and the charge which fbc adds to a species | [Section 3.4](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| chemical formula | `string` | <span id="chemical-formula"></span>the elemental composition of the species | [Section 3.4](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| charge | `double` | <span id="charge"></span>the charge of the species, counted in electrons | [Section 3.4](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| rendered substance units | `latex` | <span id="rendered-substance-units"></span>the substance units of the species rendered as a formula |
| derived units | `latex` | <span id="derived-units"></span>the units of the quantity of the species as the report derives them |

## Related elements

- [Compartment](compartment.md): a bounded space in which species are located
- [Reaction](reaction.md): a process which changes the quantities of species
- [Species reference](speciesreference.md): the participation of a species in a reaction as a reactant or a product
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.6 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
