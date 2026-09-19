# UnitDefinition

A named unit built from the base units of SBML.

A unit definition composes a unit from base units, each raised to an exponent, scaled by a power of ten and multiplied by a factor; "millimole per litre per second" is such a product. Its identifier can then be used wherever a model declares units. Unit definitions are optional and a model has to be numerically consistent without them, but they let a reader and a tool check what the numbers mean.

The report renders every unit definition as a formula, in the table and in the inspector, and lists the units it is built from in the inspector.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [listOfUnits](#listofunits) | `list` | - | the units the definition multiplies, each with its exponent, scale and multiplier | [core 4.4.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="listofunits"></span>**listOfUnits**

Every unit of the list is one factor of the definition: a base unit of SBML named by its kind, raised to the exponent, scaled by ten to the power of the scale and multiplied by the multiplier. "millimole per litre" is the mole with scale -3 times the litre with exponent -1, and "minute" is the second with multiplier 60. A definition with an empty list of units is an undefined unit, which is not the same as a dimensionless one.

The inspector of a unit definition shows the units as a table of kind, exponent, scale and multiplier next to the formula the report renders from them, so a reader sees what the file says as well as what it means.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [formula](#formula) | `latex` | the composed unit rendered as a formula |

<span id="formula"></span>**formula**

The report multiplies the base units of the definition with their exponent, scale and multiplier and renders the result as a formula, for example millimole per litre per second as a fraction.

The rendered unit is the column "units" of the table of unit definitions and the row "formula" of the inspector, above the units it is built from.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Compartment](compartment.md): a bounded space in which species are located
- [Species](species.md): a pool of a chemical entity in a compartment
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
