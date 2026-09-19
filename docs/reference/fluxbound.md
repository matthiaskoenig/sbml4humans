# FluxBound

A constraint on the flux of a reaction, as fbc Version 1 writes it.

A flux bound of the first version of the package is an object of the model which names a [reaction](reaction.md), an operation and a value, so that two of them are needed to keep a flux inside an interval and one with the operation `equal` fixes it.

Version 2 removed the construct: a [reaction](reaction.md) names the [parameters](parameter.md) of its lower and its upper bound instead, which lets other elements of the model compute a bound and keeps one bound in one place for many reactions. The report shows a flux bound only for a document which is written in Version 1, where it is the only place the capacity of a reaction is stated.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [reaction](#reaction) | [`SIdRef`](datatypes.md#sidref) | required | the reaction whose flux the bound constrains | [fbc v1 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |
| [operation](#operation) | [`FbcOperation`](datatypes.md#fbcoperation) | required | how the flux is related to the value: greaterEqual, lessEqual or equal | [fbc v1 3.2.2](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |
| [value](#value) | [`double`](datatypes.md#double) | required | the number the flux is compared with | [fbc v1 3.5](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="reaction"></span>**reaction**

The attribute is required and names a [reaction](reaction.md) of the model. The report links it, and the inspector of the reaction lists every bound which constrains it under "referenced by", which is where the capacity of a reaction of a Version 1 model is read.

- `2020404` (error): The attribute 'fbc:reaction' of a &lt;fluxBound&gt; must be of the data type SIdRef.
- `2020408` (error): The value of the attribute 'fbc:reaction' of a &lt;fluxBound&gt; object must be the identifier of an existing &lt;reaction&gt; object defined in the enclosing &lt;model&gt; object.
- `2020409` (error): The combined set of all &lt;fluxBound&gt;'s with identical values for 'fbc:reaction' must be consistent. That is while it is possible to define a lower and an upper bound for a reaction, it is not possible to define multiple lower or upper bounds.

<span id="operation"></span>**operation**

The operation says which side of the value the flux has to stay on. `greaterEqual` and `lessEqual` are the lower and the upper bound, `equal` fixes the flux at the value, which is how a measured exchange rate is written.

The report shows the operation next to the value.

- `2020406` (error): The attribute 'fbc:operation' of a &lt;fluxBound&gt; must be of the data type FbcOperation and thus it's value must be one of 'lessEqual', 'greaterEqual' or 'equal'.
- `2020409` (error): The combined set of all &lt;fluxBound&gt;'s with identical values for 'fbc:reaction' must be consistent. That is while it is possible to define a lower and an upper bound for a reaction, it is not possible to define multiple lower or upper bounds.

<span id="value"></span>**value**

The value carries the units of a reaction flux, extent per time, which the model defines globally. An infinite value states that the flux is not bounded in that direction, and the report shows it as the [sign of infinity](concepts.md#number) with the direction of that bound.

- `2020407` (error): The attribute 'fbc:value' of a &lt;fluxBound&gt; must be of the data type double.

## Validation rules

- `2010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; object the values of the attributes id and fbc:id on every instance of the following classes of objects must be unique across the set of all id and fbc:id attribute values of all such objects in a model: the model itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;fluxBound&gt;, &lt;objective&gt;, &lt;fluxObjective&gt;, &lt;geneProduct&gt; and &lt;geneProductAssociation&gt; objects defined by the Flux Balance Constraints package.
- `2020401` (error): A &lt;fluxBound&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a &lt;fluxBound&gt;.
- `2020402` (error): A &lt;fluxBound&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespace are permitted on a &lt;fluxBound&gt;.
- `2020403` (error): A &lt;fluxBound&gt; object must have the required attributes 'fbc:reaction', 'fbc:operation' and 'fbc:value', and may have the optional attributes 'fbc:id' and 'fbc:name'. No other attributes from the SBML Level 3 Flux Balance Constraints namespace are permitted on a &lt;fluxBound&gt; object.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Model](model.md): the container of everything a model is made of
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 1 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-1.release-1), Section 3.5 (Olivier and Bergmann 2013, COMBINE specification).
