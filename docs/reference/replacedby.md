# ReplacedBy

The element of a submodel which takes the place of the element carrying it.

A replaced by turns a replacement around: the element which carries it disappears and the element of the [submodel](submodel.md) it names stays, so that every reference to the element of the containing model points into the submodel afterwards. It is how a model declares a placeholder which one of its parts fills in.

An element carries at most one replaced by, and it names the element which replaces it the same four ways a [deletion](deletion.md) does, by port, identifier, unit identifier or meta id, with a [nested reference](sbaseref.md) for an element which sits deeper.

The report shows the replacement in the inspector of the element, links the submodel and the element inside it, and shows the replacement as an element of its own.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [submodelRef](#submodelref) | [`SIdRef`](datatypes.md#sidref) | required | the submodel which holds the replacing element | [comp 3.6.4](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [portRef](#portref) | [`PortSIdRef`](datatypes.md#portsidref) | optional | the port of the submodel whose element takes the place of this element | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | [`SIdRef`](datatypes.md#sidref) | optional | the element which replaces this element, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the unit definition which replaces this unit definition | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | [`IDREF`](datatypes.md#idref) | optional | the element which replaces this element, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | [`SBaseRef`](sbaseref.md) | optional | the reference which reaches into a submodel of the named submodel | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="submodelref"></span>**submodelRef**

The reference names a [submodel](submodel.md) of the model which carries the replacement. It is required, and the other references are resolved in the model that submodel instantiates.

- `1010308` (error): The value of a 'comp:submodelRef' attribute on &lt;replacedElement&gt; and &lt;replacedBy&gt; objects must always conform to the syntax of the SBML data type SId.
- `1021104` (error): The value of a 'comp:submodelRef' attribute on a &lt;replacedBy&gt; object must be the identifier of a &lt;submodel&gt; present in the &lt;replacedBy&gt; object's parent Model.

<span id="portref"></span>**portRef**

The replacement names a [port](port.md) of the model the submodel instantiates, and the element behind that port is the one which stays.

- `1020701` (error): The value of a 'comp:portRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;port&gt; object in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020706` (error): The value of a 'comp:portRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1021101` (error): A &lt;replacedBy&gt; object must point to another object; that is, a &lt;replacedBy&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef' or 'comp:metaIdRef'.
- `1021102` (error): A &lt;replacedBy&gt; object can only point to one other object; that is, a given &lt;replacedBy&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.

<span id="idref"></span>**idRef**

The identifier is resolved in the model the named submodel instantiates.

- `1020702` (error): The value of a 'comp:idRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of an object contained in (that is, within the SId namespace of) the &lt;model&gt; referenced by that &lt;sBaseRef&gt;. This includes objects with 'id' attributes defined in packages other than SBML Level 3 Core or the Hierarchical Model Composition package.
- `1020707` (error): The value of a 'comp:idRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1021101` (error): A &lt;replacedBy&gt; object must point to another object; that is, a &lt;replacedBy&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef' or 'comp:metaIdRef'.
- `1021102` (error): A &lt;replacedBy&gt; object can only point to one other object; that is, a given &lt;replacedBy&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own. The units which SBML reserves cannot replace anything.

- `1020703` (error): The value of a 'comp:unitRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;unitDefinition&lt; object contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020708` (error): The value of a 'comp:unitRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1021101` (error): A &lt;replacedBy&gt; object must point to another object; that is, a &lt;replacedBy&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef' or 'comp:metaIdRef'.
- `1021102` (error): A &lt;replacedBy&gt; object can only point to one other object; that is, a given &lt;replacedBy&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.

<span id="metaidref"></span>**metaIdRef**

This is the way to name a replacing element which carries no identifier of its own.

- `1020704` (error): The value of a 'comp:metaIdRef' attribute on an &lt;sBaseRef&gt; object must be the value of a 'comp:metaid' attribute on an element contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020709` (error): The value of a 'comp:metaIdRef' attribute on an SBaseRef object must always conform to the syntax of the XML data type ID.
- `1021101` (error): A &lt;replacedBy&gt; object must point to another object; that is, a &lt;replacedBy&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef' or 'comp:metaIdRef'.
- `1021102` (error): A &lt;replacedBy&gt; object can only point to one other object; that is, a given &lt;replacedBy&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.

<span id="sbaseref"></span>**sBaseRef**

A replacement which names a submodel of the instantiated model carries a [nested reference](sbaseref.md) which names the element inside it, so that an element of a sub-submodel takes the place of this element.

- `1020705` (error): If an &lt;sBaseRef&gt; object contains an &lt;sBaseRef&gt; child, the parent &lt;sBaseRef&gt; must point to a &lt;submodel&gt; object, or a &lt;port&gt; that itself points to a &lt;submodel&gt; object.
- `1020710` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, an SBaseRef object may only contain a single &lt;sBaseRef&gt; child.
- `1020711` (warning): The 'sbaseRef' spelling of an SBaseRef child of an SBaseRef object is considered deprecated, and 'sBaseRef' should be used instead.

## Validation rules

- `1010501` (warning): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, the units of the replaced element, multiplied by the units of any applicable conversion factor, should equal the units of the replacement element.
- `1020710` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, an SBaseRef object may only contain a single &lt;sBaseRef&gt; child.
- `1020714` (error): Any one SBML object may only be referenced in one of the following ways: referenced by a single &lt;port&gt; object; referenced by a single &lt;deletion&gt; object; referenced by a single &lt;replacedElement&gt;; be the parent of a single &lt;replacedBy&gt; child; be referenced by one or more &lt;replacedBy&gt; objects; or be referenced by one or more &lt;replacedElement&gt; objects all using the 'deletion' attribute. Essentially, once an object has been referenced in one of these ways it cannot be referenced again.
- `1021103` (error): A &lt;replacedBy&gt; object must have a value for the required attribute 'comp:submodelRef', and a value for one, and only one, of the following attributes: 'comp:portRef', 'comp:idRef', 'comp:unitRef' or 'comp:metaIdRef'. No other attributes from the HierarchicalModel Composition namespace are permitted on a &lt;replacedBy&gt; object.
- `1021201` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, the SBML class of the replacement element must match the SBML class of the replaced element, with two exceptions: an element of a derived class may replace an object of its base class (for base classes other than SBase), and any SBML class with mathematical meaning may replace a &lt;parameter&gt;. A base class may not replace a derived class, however, nor may a &lt;parameter&gt; replace some other SBML element with mathematical meaning.
- `1021202` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, if the replaced element has the 'id' attribute set, the replacement !element must also have the 'id' attribute set.
- `1021203` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, if the replaced element has the 'metaid' attribute set, the replacement element must also have the 'metaid' attribute set.
- `1021204` (error): If one element replaces another, whether it is the target of a &lt;replacedBy&gt; element, or whether it has a child &lt;replacedElement&gt;, if the replaced element has an identifier attribute from some other SBML package set, the replacement element must also have that same identifier attribute set.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [ReplacedElement](replacedelement.md): an element of a submodel which the element carrying it takes the place of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.6.4 (Smith et al. 2015, J Integr Bioinform 12(2):268).
