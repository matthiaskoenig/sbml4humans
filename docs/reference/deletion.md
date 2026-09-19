# Deletion

An element which is removed from a submodel before it is instantiated.

A deletion names one element of the model a [submodel](submodel.md) instantiates and removes it from the composed model. It is how a model uses a part of another model: the initial assignment which the containing model provides itself, the reaction which does not belong in the new context, the parameter which is set from outside.

The removal reaches further than the named element. Everything which depends on it goes with it: a species takes the species references which name it, and with them the reactions which become meaningless, and a compartment takes the species inside it.

A deletion carries an identifier of its own, so that a [replaced element](replacedelement.md) can say that it takes the place of what was deleted, and a name, because deletions are shown to modellers.

The report shows the deletions of a submodel in its inspector, links the element every one of them removes and shows each deletion as an element of its own.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [portRef](#portref) | [`PortSIdRef`](datatypes.md#portsidref) | optional | the port of the submodel whose element is removed | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | [`SIdRef`](datatypes.md#sidref) | optional | the element which is removed, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the unit definition which is removed | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | [`IDREF`](datatypes.md#idref) | optional | the element which is removed, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | [`SBaseRef`](sbaseref.md) | optional | the reference which reaches into a submodel of the submodel | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="portref"></span>**portRef**

The deletion names a [port](port.md) of the model the submodel instantiates, and the element behind that port is what is removed. Naming the port instead of the element is the friendlier way, because the port is the interface the other model offers.

- `1020701` (error): The value of a 'comp:portRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;port&gt; object in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020706` (error): The value of a 'comp:portRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1020901` (error): A &lt;deletion&gt; object must point to another object; that is, a &lt;deletion&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'
- `1020902` (error): A &lt;deletion&gt; object can only point to one other object; that is, a given &lt;deletion&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'

<span id="idref"></span>**idRef**

The identifier is resolved in the model the submodel instantiates, not in the model which declares the deletion.

- `1020702` (error): The value of a 'comp:idRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of an object contained in (that is, within the SId namespace of) the &lt;model&gt; referenced by that &lt;sBaseRef&gt;. This includes objects with 'id' attributes defined in packages other than SBML Level 3 Core or the Hierarchical Model Composition package.
- `1020707` (error): The value of a 'comp:idRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1020901` (error): A &lt;deletion&gt; object must point to another object; that is, a &lt;deletion&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'
- `1020902` (error): A &lt;deletion&gt; object can only point to one other object; that is, a given &lt;deletion&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own. The units which SBML reserves cannot be deleted.

- `1020703` (error): The value of a 'comp:unitRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;unitDefinition&lt; object contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020708` (error): The value of a 'comp:unitRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1020901` (error): A &lt;deletion&gt; object must point to another object; that is, a &lt;deletion&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'
- `1020902` (error): A &lt;deletion&gt; object can only point to one other object; that is, a given &lt;deletion&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'

<span id="metaidref"></span>**metaIdRef**

This is the way to delete an element which carries no identifier, for example a rule or a reaction written without one.

- `1020704` (error): The value of a 'comp:metaIdRef' attribute on an &lt;sBaseRef&gt; object must be the value of a 'comp:metaid' attribute on an element contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020709` (error): The value of a 'comp:metaIdRef' attribute on an SBaseRef object must always conform to the syntax of the XML data type ID.
- `1020901` (error): A &lt;deletion&gt; object must point to another object; that is, a &lt;deletion&gt; object must always have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'
- `1020902` (error): A &lt;deletion&gt; object can only point to one other object; that is, a given &lt;deletion&gt; object can only have a value for one of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'

<span id="sbaseref"></span>**sBaseRef**

A deletion which names a submodel of the instantiated model carries a [nested reference](sbaseref.md) which names the element inside it, so that an element of a sub-submodel can be removed.

- `1020705` (error): If an &lt;sBaseRef&gt; object contains an &lt;sBaseRef&gt; child, the parent &lt;sBaseRef&gt; must point to a &lt;submodel&gt; object, or a &lt;port&gt; that itself points to a &lt;submodel&gt; object.
- `1020710` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, an SBaseRef object may only contain a single &lt;sBaseRef&gt; child.
- `1020711` (warning): The 'sbaseRef' spelling of an SBaseRef child of an SBaseRef object is considered deprecated, and 'sBaseRef' should be used instead.

## Validation rules

- `1010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; or &lt;modelDefinition&gt; object, the values of the attributes id and comp:id on every instance of the following classes of objects must be unique across the set of all id and comp:id attribute values of all such objects in a model: the model itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;submodel&gt; and &lt;deletion&gt; objects defined by the Hierarchical Model Composition package, plus any objects defined by any other package with 'package:id' attributes defined as falling in the 'SId' namespace.
- `1020710` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, an SBaseRef object may only contain a single &lt;sBaseRef&gt; child.
- `1020714` (error): Any one SBML object may only be referenced in one of the following ways: referenced by a single &lt;port&gt; object; referenced by a single &lt;deletion&gt; object; referenced by a single &lt;replacedElement&gt;; be the parent of a single &lt;replacedBy&gt; child; be referenced by one or more &lt;replacedBy&gt; objects; or be referenced by one or more &lt;replacedElement&gt; objects all using the 'deletion' attribute. Essentially, once an object has been referenced in one of these ways it cannot be referenced again.
- `1020903` (error): A &lt;deletion&gt; object must have a value for one, and only one, of the attributes 'comp:portRef', 'comp:idRef', 'comp:unitRef', and 'comp:metaIdRef'. It may also have the optional attributes 'comp:id' and 'comp:name'. No other attributes from the Hierarchical Model Composition namespace are permitted on a &lt;deletion&gt; object.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [ReplacedElement](replacedelement.md): an element of a submodel which the element carrying it takes the place of
- [Port](port.md): an element of the model which other models are meant to connect to
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.5.3 (Smith et al. 2015, J Integr Bioinform 12(2):268).
