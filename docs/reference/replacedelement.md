# ReplacedElement

An element of a submodel which the element carrying it takes the place of.

A replacement is the glue of a composed model. The element which carries the replaced element stays, the element it names disappears, and every reference to the one that disappeared points at the one that stays. Two submodels are connected by letting one element of the containing model replace an element of each: the three become one.

Each replaced element names the [submodel](submodel.md) it reaches into and one element inside it, by port, identifier, unit identifier or meta id, and reaches deeper with a [nested reference](sbaseref.md). It may carry a conversion factor which rescales the replaced value, and instead of naming an element it may name a [deletion](deletion.md), which records that the element takes the place of something the submodel lost.

The report lists the replacements of an element in its inspector, links the submodel and the element inside it, and shows every replacement as an element of its own.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [submodelRef](#submodelref) | `SIdRef` | the submodel which holds the replaced element | [comp 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [deletion](#deletion) | `SIdRef` | the deletion of the submodel whose element this element takes the place of | [comp 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [conversionFactor](#conversionfactor) | `SIdRef` | the parameter which rescales the replaced value to the scale of this element | [comp 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [portRef](#portref) | `PortSIdRef` | the port of the submodel whose element is replaced | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | `SIdRef` | the element which is replaced, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | `UnitSIdRef` | the unit definition which is replaced | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | `IDREF` | the element which is replaced, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | `SBaseRef` | the reference which reaches into a submodel of the named submodel | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="submodelref"></span>**submodelRef**

The reference names a [submodel](submodel.md) of the model which carries the replacement. It is required, and it says which model the other references are resolved in: only elements of the model that submodel instantiates can be named.

<span id="deletion"></span>**deletion**

The reference names a [deletion](deletion.md) of the named submodel and takes the place of the four references: instead of an element which is replaced, the replacement names an element which was removed. It changes nothing about the composed model and nothing about its mathematics; it records the decision that this element is what the submodel lost, so that a reader, and a tool which draws the model, can follow it.

<span id="conversionfactor"></span>**conversionFactor**

The reference names a [parameter](parameter.md) of the model which carries the replacement. One unit of the replaced element multiplied by the factor is one unit of the replacing element, which is how a submodel written in millimole is used by a model written in mole. The factor applies to every reference to the replaced element, and the factors of nested replacements multiply.

A replacement cannot carry a conversion factor and a deletion at the same time: what is deleted has no value left to convert.

<span id="portref"></span>**portRef**

The replacement names a [port](port.md) of the model the submodel instantiates, and the element behind that port is what is replaced. It is the first choice of the specification, because the port is the interface the other model offers.

<span id="idref"></span>**idRef**

The identifier is resolved in the model the named submodel instantiates. It is the choice for an element which no port exposes.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own. The units which SBML reserves cannot be replaced.

<span id="metaidref"></span>**metaIdRef**

This is the way to replace an element which carries no identifier of its own.

<span id="sbaseref"></span>**sBaseRef**

A replacement which names a submodel of the instantiated model carries a [nested reference](sbaseref.md) which names the element inside it, so that an element of a sub-submodel can be replaced.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [ReplacedBy](replacedby.md): the element of a submodel which takes the place of the element carrying it
- [Deletion](deletion.md): an element which is removed from a submodel before it is instantiated
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.6.2 (Smith et al. 2015, J Integr Bioinform 12(2):268).
