# Local parameter

A named value which only one kinetic law uses.

A local parameter is defined inside a kinetic law and can only be used by its formula, which keeps a constant that belongs to one reaction out of the global parameters. Its identifier lives in the namespace of the reaction and takes precedence over a global element of the same name inside the formula.

The report shows a local parameter as an element of its own, with its value, its units and the reaction it belongs to.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| value | `double` | <span id="value"></span>the value of the local parameter | [Section 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| units | `UnitSIdRef` | <span id="units"></span>the units of the value of the local parameter | [Section 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| rendered units | `latex` | <span id="rendered-units"></span>the units of the local parameter rendered as a formula |
| derived units | `latex` | <span id="derived-units"></span>the units of the value as the report derives them |

## Related elements

- [Kinetic law](kineticlaw.md): the formula which gives the speed of a reaction
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.6 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
