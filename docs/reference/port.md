# Port

An element of the model which other models are meant to connect to.

A port gives a name to one element of the model and declares it as an intended point of interaction, so that a model which includes this one connects to the port instead of reaching into the model. Port identifiers live in a namespace of their own, which is why a port may carry the same identifier as an element of the model.

Exactly one of the four references of a port is set, and each of them names the element in a different way. The use of ports is advisory in this version of the package, nothing enforces it.

The report shows which element a port names, links it, and lists the ports of a model in a section of their own.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [portRef](#portref) | [`PortSIdRef`](datatypes.md#portsidref) | optional | the port which this reference names | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | [`SIdRef`](datatypes.md#sidref) | optional | the element which this port names, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | [`UnitSIdRef`](datatypes.md#unitsidref) | optional | the unit definition which this port names | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | [`IDREF`](datatypes.md#idref) | optional | the element which this port names, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | [`SBaseRef`](sbaseref.md) | optional | the reference which reaches from the named submodel into the model it instantiates | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="portref"></span>**portRef**

A port reference names a port instead of an element. A port may not name another port of its own model, so a model which passes on the interface of one of its parts names the submodel and reaches into it with the nested reference of the package, whose port reference then names the port inside that submodel. Port identifiers are a namespace of their own, and the reference is resolved among the ports of the model it reaches into.

The report shows the port reference as text; it does not follow it into another model.

- `1020701` (error): The value of a 'comp:portRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;port&gt; object in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020706` (error): The value of a 'comp:portRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.

<span id="idref"></span>**idRef**

This is the usual way to define a port: the identifier of the species, the parameter, the compartment or the reaction which the port stands for. Since a port of a model must name an element of that same model, the identifier is resolved in this model.

The report links the element the port names.

- `1020702` (error): The value of a 'comp:idRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of an object contained in (that is, within the SId namespace of) the &lt;model&gt; referenced by that &lt;sBaseRef&gt;. This includes objects with 'id' attributes defined in packages other than SBML Level 3 Core or the Hierarchical Model Composition package.
- `1020707` (error): The value of a 'comp:idRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1020801` (error): A &lt;port&gt; object must point to another object; that is, a &lt;port&gt; object must always have a value for one of the attributes 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.
- `1020802` (error): A &lt;port&gt; object can only point to one other object; that is, a given &lt;port&gt; object can only have a value for one of the attributes 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own, so naming a [unit definition](unitdefinition.md) needs an attribute of its own. The units which SBML reserves cannot be named here: they can neither be replaced nor deleted.

The report links the unit definition the port names.

- `1020703` (error): The value of a 'comp:unitRef' attribute on an &lt;sBaseRef&gt; object must be the identifier of a &lt;unitDefinition&lt; object contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020708` (error): The value of a 'comp:unitRef' attribute on an SBaseRef object must always conform to the syntax of the SBML data type SId.
- `1020801` (error): A &lt;port&gt; object must point to another object; that is, a &lt;port&gt; object must always have a value for one of the attributes 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.
- `1020802` (error): A &lt;port&gt; object can only point to one other object; that is, a given &lt;port&gt; object can only have a value for one of the attributes 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.

<span id="metaidref"></span>**metaIdRef**

Every element of a file may carry a meta id, and this is the way to name an element which has no identifier, for example a rule or a reaction which was written without one.

The report searches the element with that meta id in the model and links it.

- `1020704` (error): The value of a 'comp:metaIdRef' attribute on an &lt;sBaseRef&gt; object must be the value of a 'comp:metaid' attribute on an element contained in the &lt;model&gt; referenced by that &lt;sBaseRef&gt;.
- `1020709` (error): The value of a 'comp:metaIdRef' attribute on an SBaseRef object must always conform to the syntax of the XML data type ID.
- `1020801` (error): A &lt;port&gt; object must point to another object; that is, a &lt;port&gt; object must always have a value for one of the attributes 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.
- `1020802` (error): A &lt;port&gt; object can only point to one other object; that is, a given &lt;port&gt; object can only have a value for one of the attributes 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'.

<span id="sbaseref"></span>**sBaseRef**

A port which names a submodel of its model can reach through it with a [nested reference](sbaseref.md), so that the port stands for an element buried inside that submodel. The chain may be of any length, one link per submodel it passes.

The report shows the chain in the inspector of the port and links the element at its end.

- `1020705` (error): If an &lt;sBaseRef&gt; object contains an &lt;sBaseRef&gt; child, the parent &lt;sBaseRef&gt; must point to a &lt;submodel&gt; object, or a &lt;port&gt; that itself points to a &lt;submodel&gt; object.
- `1020711` (warning): The 'sbaseRef' spelling of an SBaseRef child of an SBaseRef object is considered deprecated, and 'sBaseRef' should be used instead.

## Validation rules

- `1010303` (error): Within &lt;model&gt; and &lt;modelDefinition&gt; objects inside an SBML document, the value of the attribute 'comp:id' on every instance of a &lt;port&gt; object must be unique across the set of all 'comp:id' attribute values of all such objects in the model.
- `1020710` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, an SBaseRef object may only contain a single &lt;sBaseRef&gt; child.
- `1020714` (error): Any one SBML object may only be referenced in one of the following ways: referenced by a single &lt;port&gt; object; referenced by a single &lt;deletion&gt; object; referenced by a single &lt;replacedElement&gt;; be the parent of a single &lt;replacedBy&gt; child; be referenced by one or more &lt;replacedBy&gt; objects; or be referenced by one or more &lt;replacedElement&gt; objects all using the 'deletion' attribute. Essentially, once an object has been referenced in one of these ways it cannot be referenced again.
- `1020803` (error): A &lt;port&gt; object must have a value for the required attribute 'comp:id', and one, and only one, of the attributes 'comp:idRef', 'comp:unitRef', or 'comp:metaIdRef'. No other attributes from the Hierarchical Model Composition namespace are permitted on a &lt;port&gt; object.
- `1020804` (error): Port definitions must be unique; that is, no two &lt;port&gt; objects in a given Model may reference the same object in that Model.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [Model](model.md): the container of everything a model is made of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.4.3 (Smith et al. 2015, J Integr Bioinform 12(2):268).
