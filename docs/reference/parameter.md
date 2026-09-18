# Parameter

A named value which the mathematics of the model can use.

A parameter associates an identifier with a numerical value, and the flag "constant" decides whether it is a constant of the model or another variable of it. Kinetic constants, thresholds and conversion factors are parameters, and so is a quantity which a rule computes over time.

The report shows the value of a parameter, its units and the units it derives, and links every element which references it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [value](#value) | `double` | the value of the parameter at the start of the simulation | [core 4.7.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [units](#units) | `UnitSIdRef` | the units of the value of the parameter | [core 4.7.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [constant](#constant) | `boolean` | whether the value of the parameter stays fixed during a simulation | [core 4.7.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="value"></span>**value**

The value is a literal number. It is optional: a missing value means that it is unknown or that it is computed by an initial assignment or a rule, which can express things a literal number cannot.

The report shows the value in the table and in the inspector.

<span id="units"></span>**units**

The units are a unit definition of the model or a base unit. A parameter inherits nothing from the model: when it declares no units, its value has none, which is why the units of a formula which uses it cannot always be checked.

The report links the referenced unit definition and renders it as a formula.

<span id="constant"></span>**constant**

A constant parameter keeps its value for the whole simulation and can only be set by an initial assignment. A parameter which is not constant is a variable of the model and is computed by a rule or changed by an event.

The report shows the flag as a mark in the column "constant".

## In the report

| field | type | meaning |
| --- | --- | --- |
| [rendered units](#rendered-units) | `latex` | the units of the parameter rendered as a formula |
| [derived units](#derived-units) | `latex` | the units of the value as the report derives them |

<span id="rendered-units"></span>**rendered units**

The report resolves the unit definition the parameter references and renders it as a formula next to its identifier.

<span id="derived-units"></span>**derived units**

The report resolves the units of the parameter and renders them as a formula. A parameter without units is shown without derived units, because there is nothing to inherit.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Unit definition](unitdefinition.md): a named unit built from the base units of SBML
- [Local parameter](localparameter.md): a named value which only one kinetic law uses

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.7 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
