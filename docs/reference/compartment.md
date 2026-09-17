# Compartment

A bounded space in which species are located.

A compartment is the place where something is: a cell, an organelle, a membrane, the extracellular space. Every species of a model has to be located in one, which is why a model with species always has at least one compartment. A compartment does not have to correspond to a physical structure, it is whatever the model treats as one well mixed space.

The report shows the size of a compartment, the units of that size and the units it derives, and links the species which are located in it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| spatial dimensions | `double` | <span id="spatial-dimensions"></span>the number of dimensions of the compartment | [Section 4.5.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| size | `double` | <span id="size"></span>the size of the compartment at the start of the simulation | [Section 4.5.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| units | `UnitSIdRef` | <span id="units"></span>the units of the size of the compartment | [Section 4.5.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| constant | `boolean` | <span id="constant"></span>whether the size of the compartment stays fixed during a simulation | [Section 4.5.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| rendered units | `latex` | <span id="rendered-units"></span>the units of the size rendered as a formula |
| derived units | `latex` | <span id="derived-units"></span>the units of the size as the report derives them |

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Species](species.md): a pool of a chemical entity in a compartment
- [Unit definition](unitdefinition.md): a named unit built from the base units of SBML

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
