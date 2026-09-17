# Unit definition

A named unit built from the base units of SBML.

A unit definition composes a unit from base units, each raised to an exponent, scaled by a power of ten and multiplied by a factor; "millimole per litre per second" is such a product. Its identifier can then be used wherever a model declares units. Unit definitions are optional and a model has to be numerically consistent without them, but they let a reader and a tool check what the numbers mean.

The report renders every unit definition as a formula instead of listing its parts, both in the table and in the inspector.

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [units](#units) | `latex` | the composed unit rendered as a formula |

<span id="units"></span>**units**

The report multiplies the base units of the definition with their exponent, scale and multiplier and renders the result as a formula, for example as mmol l^-1 s^-1.

The rendered unit is the column "units" of the table of unit definitions and the row "units" of the inspector.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [Compartment](compartment.md): a bounded space in which species are located
- [Species](species.md): a pool of a chemical entity in a compartment
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
