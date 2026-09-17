# Species

A pool of a chemical entity in a compartment.

A species is a pool of entities which the model treats as indistinguishable: a metabolite, a protein, an ion, a gene. It is located in exactly one [compartment](compartment.md), it may participate in reactions, and its quantity is what most simulations compute. The quantity is an amount or a concentration, depending on the attribute "only substance units".

The report shows the initial quantity of a species, its units, the flags which say how it may change, and links its compartment and every reaction it takes part in.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [compartment](#compartment) | `SIdRef` | the compartment the species is located in | [core 4.6.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initial amount](#initial-amount) | `double` | the amount of the species when the simulation starts | [core 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [initial concentration](#initial-concentration) | `double` | the concentration of the species when the simulation starts | [core 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [substance units](#substance-units) | `UnitSIdRef` | the units of the amount of the species | [core 4.6.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [only substance units](#only-substance-units) | `boolean` | whether the identifier of the species stands for an amount instead of a concentration | [core 4.6.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [boundary condition](#boundary-condition) | `boolean` | whether the quantity of the species is left unchanged by the reactions | [core 4.6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constant](#constant) | `boolean` | whether the quantity of the species stays fixed during a simulation | [core 4.6.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [conversion factor](#conversion-factor) | `SIdRef` | the parameter which converts the extent of a reaction into the quantity of the species | [core 4.6.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [fbc](#fbc) | `SpeciesFbc` | the chemical formula and the charge which fbc adds to a species | [fbc 3.4](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| [chemical formula](#chemical-formula) | `string` | the elemental composition of the species | [fbc 3.4](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| [charge](#charge) | `integer` | the charge of the species, counted in electrons | [fbc 3.4](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="compartment"></span>**compartment**

Every species names the compartment it is in; SBML has no default compartment. The size of that compartment is what converts between the amount and the concentration of the species.

The report links the compartment in the table and in the inspector.

<span id="initial-amount"></span>**initial amount**

The initial amount is the quantity of the species at the start of a simulation, measured in its substance units. A species sets either an initial amount or an initial concentration, never both, and it may set neither, in which case the value comes from an initial assignment or a rule.

The report shows the initial amount in the table and in the inspector.

<span id="initial-concentration"></span>**initial concentration**

The initial concentration is the amount of the species divided by the size of its compartment at the start of a simulation. It excludes the initial amount, a species sets at most one of the two.

The report shows the initial concentration in the table and in the inspector.

<span id="substance-units"></span>**substance units**

The substance units say what a quantity of one means, for example one mole, one millimole or one item. When the species does not declare them, it inherits the substance units of the model.

The report links the referenced unit definition and renders it as a formula.

<span id="only-substance-units"></span>**only substance units**

This flag decides what the identifier of the species means when it appears in a formula: with "true" it is an amount, with "false" it is an amount divided by the size of its compartment, that is a concentration. The flag is needed as its own attribute because the initial quantity and the units are both optional.

The report shows the flag as a mark in the column "only substance units" and uses it when it derives the units of the species.

<span id="boundary-condition"></span>**boundary condition**

A species on the boundary of the reaction system may appear as a reactant or a product, but the reactions do not determine its quantity; it is held by the modeller, for example as a constant supply of glucose. A species which is not a boundary condition is changed by every reaction it takes part in.

The report shows the flag as a mark in the column "boundary condition".

<span id="constant"></span>**constant**

A constant species keeps its quantity for the whole simulation, whatever happens around it, and only an initial assignment may set it. Together with the boundary condition, the flag says whether the species is a variable of the model or a given value.

The report shows the flag as a mark in the column "constant".

<span id="conversion-factor"></span>**conversion factor**

When the amount of a species is not measured in the extent units of the reactions, a constant parameter states the factor between the two, instead of leaving the conversion implicit. A factor on the species overrides the one of the model.

The report shows the referenced parameter with its value in the attributes of the species.

<span id="fbc"></span>**fbc**

A constraint based model needs the elemental composition and the charge of a species to check that its reactions are balanced. Both are annotations of the species in the sense that they do not enter the mathematics of the model.

The report shows them in the inspector of a species of a model which uses fbc.

<span id="chemical-formula"></span>**chemical formula**

The formula should consist of atomic names of the periodic table, ordered by the Hill system: the carbon atoms first, then the hydrogen atoms, then every other element in alphabetical order, each followed by its count. `C10H12N5O13P3` is such a formula. Where a compound has an undefined or generic component, the symbols `R` and `X` stand for it.

The report shows the formula in the inspector of the species.

<span id="charge"></span>**charge**

The charge is given in electrons, not in coulombs, and it is the charge of one entity of the species. Together with the chemical formula it is what a check of the charge balance of a reaction needs.

The report shows the charge in the inspector of the species.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered substance units](#rendered-substance-units) | `latex` | the substance units of the species rendered as a formula |
| [derived units](#derived-units) | `latex` | the units of the quantity of the species as the report derives them |

<span id="rendered-substance-units"></span>**rendered substance units**

The report resolves the unit definition the species references and renders it as a formula next to its identifier.

<span id="derived-units"></span>**derived units**

The report derives the units of a species from its substance units, from the units of its compartment and from the flag "only substance units", and renders the result as a formula. This is the unit a formula sees when it uses the identifier of the species.

## Related elements

- [Compartment](compartment.md): a bounded space in which species are located
- [Reaction](reaction.md): a process which changes the quantities of species
- [Species reference](speciesreference.md): the participation of a species in a reaction as a reactant or a product
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.6 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
