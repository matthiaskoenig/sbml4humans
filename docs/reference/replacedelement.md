# ReplacedElement

An element of a submodel which the element carrying it takes the place of.

A replacement is the glue of a composed model. The element which carries the replaced element stays, the element it names disappears, and every reference to the one that disappeared points at the one that stays. Two submodels are connected by letting one element of the containing model replace an element of each: the three become one.

Each replaced element names the [submodel](submodel.md) it reaches into and one element inside it, by port, identifier, unit identifier or meta id, and reaches deeper with a [nested reference](sbaseref.md). It may carry a conversion factor which rescales the replaced value, and instead of naming an element it may name a [deletion](deletion.md), which records that the element takes the place of something the submodel lost.

The report lists the replacements of an element in its inspector, links the submodel and the element inside it, and shows every replacement as an element of its own.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [submodelRef](#submodelref) | [`SIdRef`](datatypes.md#sidref) | required | the submodel which holds the replaced element | [comp 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [deletion](#deletion) | [`SIdRef`](datatypes.md#sidref) | optional | the deletion of the submodel whose element this element takes the place of | [comp 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [conversionFactor](#conversionfactor) | [`SIdRef`](datatypes.md#sidref) | optional | the parameter which rescales the replaced value to the scale of this element | [comp 3.6.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [portRef](#portref) | [`PortSIdRef`](datatypes.md#portsidref) | optional | the port of the submodel whose element is replaced | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | [`SIdRef`](datatypes.md#sidref) | optional | the element which is replaced, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the unit definition which is replaced | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | [`IDREF`](datatypes.md#idref) | optional | the element which is replaced, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | [`SBaseRef`](sbaseref.md) | optional | the reference which reaches into a submodel of the named submodel | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="submodelref"></span>**submodelRef**

The reference names a [submodel](submodel.md) of the model which carries the replacement. It is required, and it says which model the other references are resolved in: only elements of the model that submodel instantiates can be named.

- `1010308` (error): The value of a 'comp:submodelRef' attribute on &lt;replacedElement&gt; and &lt;replacedBy&gt; objects must always conform to the syntax of the SBML data type SId.
- `1021004` (error): The value of a 'comp:submodelRef' attribute on a &lt;replacedElement&gt; object must be the identifier of a &lt;submodel&gt; present in the &lt;replacedElement&gt; object's parent Model.

<span id="deletion"></span>**deletion**

The reference names a [deletion](deletion.md) of the named submodel and takes the place of the four references: instead of an element which is replaced, the replacement names an element which was removed. It changes nothing about the composed model and nothing about its mathematics; it records the decision that this element is what the submodel lost, so that a reader, and a tool which draws the model, can follow it.

- `1010309` (error): The value of a 'comp:deletion' attribute on &lt;replacedElement&gt; objects must always conform to the syntax of the SBML data type SId.
- `1021001` (error): A &lt;replacedElement&gt; object must point to another object; that is, a &lt;replacedElement&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.
- `1021002` (error): A &lt;replacedElement&gt; object can only point to one other object; that is, a given &lt;replacedElement&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.
- `1021005` (error): The value of a 'comp:deletion' attribute on a &lt;replacedElement&gt; object must be the identifier of a &lt;deletion&gt; present in the &lt;replacedElement&gt; object's parent Model.
- `1021011` (error): If a &lt;replacedElement&gt; uses the 'comp:deletion' attribute, then it should not also use the 'comp:conversionFactor' attribute.

<span id="conversionfactor"></span>**conversionFactor**

The reference names a [parameter](parameter.md) of the model which carries the replacement. One unit of the replaced element multiplied by the factor is one unit of the replacing element, which is how a submodel written in millimole is used by a model written in mole. The factor applies to every reference to the replaced element, and the factors of nested replacements multiply.

A replacement cannot carry a conversion factor and a deletion at the same time: what is deleted has no value left to convert.

Default: the value of the replaced element is taken over unchanged, apart from the conversion factors of the submodel.

- `1010310` (error): The value of a 'comp:conversionFactor' attribute on &lt;replacedElement&gt; objects must always conform to the syntax of the SBML data type SId.
- `1021006` (error): The value of a 'comp:conversionFactor' attribute on a &lt;replacedElement&gt; object must be the identifier of a &lt;parameter&gt; present in the &lt;replacedElement&gt; object's parent Model
- `1021011` (error): If a &lt;replacedElement&gt; uses the 'comp:deletion' attribute, then it should not also use the 'comp:conversionFactor' attribute.

<span id="portref"></span>**portRef**

The replacement names a [port](port.md) of the model the submodel instantiates, and the element behind that port is what is replaced. It is the first choice of the specification, because the port is the interface the other model offers.

- `1020701` (error): The value of a 'comp:portRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;port&gt; object in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020706` (error): The value of a 'comp:portRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1021001` (error): A &lt;replacedElement&gt; object must point to another object; that is, a &lt;replacedElement&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.
- `1021002` (error): A &lt;replacedElement&gt; object can only point to one other object; that is, a given &lt;replacedElement&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.

<span id="idref"></span>**idRef**

The identifier is resolved in the model the named submodel instantiates. It is the choice for an element which no port exposes.

- `1020702` (error): The value of a 'comp:idRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of an object contained in (that is, within the SId namespace of) the &lt;model&gt; referenced by that &lt;sBaseRef&gt;. This includes objects with 'id' attributes defined in packages other than SBML Level 3 Core or the Hierarchical Model Composition package.
- `1020707` (error): The value of a 'comp:idRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1021001` (error): A &lt;replacedElement&gt; object must point to another object; that is, a &lt;replacedElement&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.
- `1021002` (error): A &lt;replacedElement&gt; object can only point to one other object; that is, a given &lt;replacedElement&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own. The units which SBML reserves cannot be replaced.

- `1020703` (error): The value of a 'comp:unitRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;unitDefinition&lt; object contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020708` (error): The value of a 'comp:unitRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1021001` (error): A &lt;replacedElement&gt; object must point to another object; that is, a &lt;replacedElement&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.
- `1021002` (error): A &lt;replacedElement&gt; object can only point to one other object; that is, a given &lt;replacedElement&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.

<span id="metaidref"></span>**metaIdRef**

This is the way to replace an element which carries no identifier of its own.

- `1020704` (error): The value of a 'comp:metaIdRef' attribute on an &lt;sBaseRef&gt; object must be the value of a 'comp:metaid' attribute on an element contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020709` (error): The value of a 'comp:metaIdRef' attribute on an SBaseRef object must always conform to the syntax of the XML data type ID.
- `1021001` (error): A &lt;replacedElement&gt; object must point to another object; that is, a &lt;replacedElement&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.
- `1021002` (error): A &lt;replacedElement&gt; object can only point to one other object; that is, a given &lt;replacedElement&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef' or 'comp:deletion'.

<span id="sbaseref"></span>**sBaseRef**

A replacement which names a submodel of the instantiated model carries a [nested reference](sbaseref.md) which names the element inside it, so that an element of a sub-submodel can be replaced.

- `1020705` (error): If an &lt;sBaseRef&gt; object contains an &lt;sBaseRef&gt; child, the parent &lt;sBaseRef&gt; must point to a &lt;submodel&gt; object, or a &lt;port&gt; that itself points to a &lt;submodel&gt; object.
- `1020711` (warning): The 'sbaseRef' spelling of an SBaseRef child of an SBaseRef object is considered deprecated, and 'sBaseRef' should be used instead.

## Validation rules

- `1010501` (warning): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, the units of the replaced element, multiplied by the units of any applicable conversion factor, should equal the units of the replacement element.
- `1020710` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, an SBaseRef object may only contain a single &lt;sBaseRef&gt; child.
- `1020714` (error): Any one SBML object may only be referenced in one of the following ways: referenced by a single &lt;port&gt; object; referenced by a single &lt;deletion&gt; object; referenced by a single &lt;replacedElement&gt;; be the parent of a single &lt;replacedBy&gt; child; be referenced by one or more &lt;replacedBy&gt; objects; or be referenced by one or more &lt;replacedElement&gt; objects all using the 'deletion' attribute. Essentially, once an object has been referenced in one of these ways it cannot be referenced again.
- `1021003` (error): A &lt;replacedElement&gt; object must have a value for the required attribute 'comp:submodelRef', and a value for one, and only one, of the following attributes: 'comp:portRef', 'comp:idRef', 'comp:unitRef', 'comp:metaIdRef', or 'comp:deletion'. It may also have a value for the optional attribute 'comp:conversionFactor'. No other attributes from the HierarchicalModel Composition namespace are permitted on a &lt;replacedElement&gt; object.
- `1021010` (error): No two &lt;replacedElement&gt; objects in the same Model may reference the same object unless that object is a &lt;deletion&gt;
- `1021201` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, the SBML class of the replacement element must match the SBML class of the replaced element, with two exceptions: an element of a derived class may replace an object of its base class (for base classes other than SBase), and any SBML class with mathematical meaning may replace a &lt;parameter&gt;. A base class may not replace a derived class, however, nor may a &lt;parameter&gt; replace some other SBML element with mathematical meaning.
- `1021202` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, if the replaced element has the 'id' attribute set, the replacement !element must also have the 'id' attribute set.
- `1021203` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, if the replaced element has the 'metaid' attribute set, the replacement element must also have the 'metaid' attribute set.
- `1021204` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, if the replaced element has an identifier attribute from some other SBML package set, the replacement element must also have that same identifier attribute set.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [ReplacedBy](replacedby.md): the element of a submodel which takes the place of the element carrying it
- [Deletion](deletion.md): an element which is removed from a submodel before it is instantiated
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.6.2 (Smith et al. 2015, J Integr Bioinform 12(2):268).
