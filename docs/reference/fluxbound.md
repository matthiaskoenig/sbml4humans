# Flux bound

A constraint on the flux of a reaction, as fbc Version 1 writes it.

A flux bound of the first version of the package is an object of the model which names a [reaction](reaction.md), an operation and a value, so that two of them are needed to keep a flux inside an interval and one with the operation `equal` fixes it.

Version 2 removed the construct: a [reaction](reaction.md) names the [parameters](parameter.md) of its lower and its upper bound instead, which lets other elements of the model compute a bound and keeps one bound in one place for many reactions. The report shows a flux bound only for a document which is written in Version 1, where it is the only place the capacity of a reaction is stated.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [reaction](#reaction) | `SIdRef` | the reaction whose flux the bound constrains | [fbc v1 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |
| [operation](#operation) | `FbcOperation` | how the flux is related to the value: greaterEqual, lessEqual or equal | [fbc v1 3.2.2](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |
| [value](#value) | `double` | the number the flux is compared with | [fbc v1 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="reaction"></span>**reaction**

The attribute is required and names a [reaction](reaction.md) of the model. The report links it, and the inspector of the reaction lists every bound which constrains it under "referenced by", which is where the capacity of a reaction of a Version 1 model is read.

<span id="operation"></span>**operation**

The operation says which side of the value the flux has to stay on. `greaterEqual` and `lessEqual` are the lower and the upper bound, `equal` fixes the flux at the value, which is how a measured exchange rate is written.

The report shows the operation next to the value.

<span id="value"></span>**value**

The value carries the units of a reaction flux, extent per time, which the model defines globally. An infinite value states that the flux is not bounded in that direction; the report cannot show it, because infinity is not a number JSON carries, and leaves the cell empty.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Model](model.md): the container of everything a model is made of
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 1 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1), Section 3.5 (Olivier and Bergmann 2013, COMBINE specification).
