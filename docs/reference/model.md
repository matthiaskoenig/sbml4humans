# Model

The container of everything a model is made of.

The model holds the lists of every element: the unit definitions, the compartments, the species, the parameters, the initial assignments, the rules, the constraints, the reactions and the events. It also sets the units which the elements inherit when they do not declare their own, in particular the unit of time, which exists nowhere else.

The report shows the model as the root of the report, its lists as the sections of the report, and its units in the attributes of the inspector.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| substance units | `UnitSIdRef` | <span id="substance-units"></span>the units of the amounts of the species which do not declare their own | [Section 4.2.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| time units | `UnitSIdRef` | <span id="time-units"></span>the unit in which time is measured in the model | [Section 4.2.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| volume units | `UnitSIdRef` | <span id="volume-units"></span>the units of the size of the compartments with three dimensions | [Section 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| area units | `UnitSIdRef` | <span id="area-units"></span>the units of the size of the compartments with two dimensions | [Section 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| length units | `UnitSIdRef` | <span id="length-units"></span>the units of the size of the compartments with one dimension | [Section 4.2.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| extent units | `UnitSIdRef` | <span id="extent-units"></span>the units in which the extent of a reaction is measured | [Section 4.2.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| conversion factor | `SIdRef` | <span id="conversion-factor"></span>the parameter which converts between the units of a species and the extent of a reaction | [Section 4.2.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| function definitions | `list` | <span id="function-definitions"></span>the user defined functions of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| unit definitions | `list` | <span id="unit-definitions"></span>the units the model defines | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| compartments | `list` | <span id="compartments"></span>the compartments of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| species | `list` | <span id="species"></span>the species of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| parameters | `list` | <span id="parameters"></span>the global parameters of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| initial assignments | `list` | <span id="initial-assignments"></span>the initial assignments of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| rules | `list` | <span id="rules"></span>the assignment, rate and algebraic rules of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| constraints | `list` | <span id="constraints"></span>the constraints of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| reactions | `list` | <span id="reactions"></span>the reactions of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| events | `list` | <span id="events"></span>the events of the model | [Section 4.2.7](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| submodels | `list` | <span id="submodels"></span>the models which this model instantiates | [Section 3.4.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| ports | `list` | <span id="ports"></span>the elements of the model which are meant to be used from outside | [Section 3.4.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| gene products | `list` | <span id="gene-products"></span>the genes and gene products the reactions of the model depend on | [Section 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| objectives | `list` | <span id="objectives"></span>the objective functions of the constraint based model | [Section 3.3.1](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| kind | `string` | <span id="kind"></span>whether the model is the model of the document or a model definition |
| rendered substance units | `latex` | <span id="rendered-substance-units"></span>the substance units of the model rendered as a formula |
| rendered time units | `latex` | <span id="rendered-time-units"></span>the time units of the model rendered as a formula |
| rendered volume units | `latex` | <span id="rendered-volume-units"></span>the volume units of the model rendered as a formula |
| rendered area units | `latex` | <span id="rendered-area-units"></span>the area units of the model rendered as a formula |
| rendered length units | `latex` | <span id="rendered-length-units"></span>the length units of the model rendered as a formula |
| rendered extent units | `latex` | <span id="rendered-extent-units"></span>the extent units of the model rendered as a formula |

## Related elements

- [Document](sbmldocument.md): the container of an SBML file, with its level, version and packages
- [Compartment](compartment.md): a bounded space in which species are located
- [Species](species.md): a pool of a chemical entity in a compartment
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.2 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
