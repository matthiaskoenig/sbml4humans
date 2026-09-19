# Compartment

A bounded space in which species are located.

A compartment is the place where something is: a cell, an organelle, a membrane, the extracellular space. Every species of a model has to be located in one, which is why a model with species always has at least one compartment. A compartment does not have to correspond to a physical structure, it is whatever the model treats as one well mixed space.

The report shows the size of a compartment, the units of that size and the units it derives, and links the species which are located in it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [spatialDimensions](#spatialdimensions) | `double` | - | the number of dimensions of the compartment | [core 4.5.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [size](#size) | `double` | - | the size of the compartment at the start of the simulation | [core 4.5.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [units](#units) | `UnitSIdRef` | - | the units of the size of the compartment | [core 4.5.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constant](#constant) | `boolean` | - | whether the size of the compartment stays fixed during a simulation | [core 4.5.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="spatialdimensions"></span>**spatialDimensions**

Three dimensions means the size is a volume, two means an area, one means a length. The value does not enter the mathematics of the model, but it decides which units of the model a compartment inherits when it does not declare its own.

The report shows the dimensions in the column "dimensions" and in the inspector.

<span id="size"></span>**size**

The size is the volume, the area or the length of the compartment, depending on its dimensions. It is optional: a missing size means that the value is unknown or that it is computed by an initial assignment or a rule, it does not mean one. When the compartment is not constant, the size can change during a simulation.

The report shows the size in the table and in the inspector, and the identifier of a compartment stands for its size in every formula of the model.

<span id="units"></span>**units**

The units are either a unit definition of the model or one of the base units. When they are not declared, the compartment inherits the volume, area or length units of the model according to its dimensions, and when the model does not declare those either, the size has no units.

The report links the referenced unit definition and renders it as a formula.

<span id="constant"></span>**constant**

A constant compartment keeps its size for the whole simulation and can only be given a value by an initial assignment. A compartment which is not constant can be changed by a rule or by an event, which is how a growing cell is modelled.

The report shows the flag as a mark in the column "constant".

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered units](#rendered-units) | `latex` | the units of the size rendered as a formula |
| [derived units](#derived-units) | `latex` | the units of the size as the report derives them |

<span id="rendered-units"></span>**rendered units**

The report resolves the unit definition the compartment references and renders it as a formula, so that the table shows the unit itself and not only its identifier.

<span id="derived-units"></span>**derived units**

The report derives the units of a compartment from its own units, or from the units of the model which it inherits, and renders them as a formula. Derived units make it visible what a value means even when the model does not declare units everywhere.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Species](species.md): a pool of a chemical entity in a compartment
- [UnitDefinition](unitdefinition.md): a named unit built from the base units of SBML

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
