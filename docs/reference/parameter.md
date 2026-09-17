# Parameter

A named value which the mathematics of the model can use.

A parameter associates an identifier with a numerical value, and the flag "constant" decides whether it is a constant of the model or another variable of it. Kinetic constants, thresholds and conversion factors are parameters, and so is a quantity which a rule computes over time.

The report shows the value of a parameter, its units and the units it derives, and links every element which references it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| value | `double` | <span id="value"></span>the value of the parameter at the start of the simulation | [Section 4.7.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| units | `UnitSIdRef` | <span id="units"></span>the units of the value of the parameter | [Section 4.7.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| constant | `boolean` | <span id="constant"></span>whether the value of the parameter stays fixed during a simulation | [Section 4.7.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| rendered units | `latex` | <span id="rendered-units"></span>the units of the parameter rendered as a formula |
| derived units | `latex` | <span id="derived-units"></span>the units of the value as the report derives them |

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Unit definition](unitdefinition.md): a named unit built from the base units of SBML
- [Local parameter](localparameter.md): a named value which only one kinetic law uses

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.7 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
