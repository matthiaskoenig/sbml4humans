# Port

An element of the model which other models are meant to connect to.

A port gives a name to one element of the model and declares it as an intended point of interaction, so that a model which includes this one connects to the port instead of reaching into the model. Port identifiers live in a namespace of their own, which is why a port may carry the same identifier as an element of the model.

Exactly one of the four references of a port is set, and each of them names the element in a different way. The use of ports is advisory in this version of the package, nothing enforces it.

The report shows which element a port names, links it, and lists the ports of a model in a section of their own.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [portRef](#portref) | `PortSIdRef` | the port which this reference names | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | `SIdRef` | the element which this port names, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | `UnitSIdRef` | the unit definition which this port names | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | `IDREF` | the element which this port names, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | `SBaseRef` | the reference which reaches from the named submodel into the model it instantiates | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="portref"></span>**portRef**

A port reference names a port instead of an element. A port may not name another port of its own model, so a model which passes on the interface of one of its parts names the submodel and reaches into it with the nested reference of the package, whose port reference then names the port inside that submodel. Port identifiers are a namespace of their own, and the reference is resolved among the ports of the model it reaches into.

The report shows the port reference as text; it does not follow it into another model.

<span id="idref"></span>**idRef**

This is the usual way to define a port: the identifier of the species, the parameter, the compartment or the reaction which the port stands for. Since a port of a model must name an element of that same model, the identifier is resolved in this model.

The report links the element the port names.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own, so naming a [unit definition](unitdefinition.md) needs an attribute of its own. The units which SBML reserves cannot be named here: they can neither be replaced nor deleted.

The report links the unit definition the port names.

<span id="metaidref"></span>**metaIdRef**

Every element of a file may carry a meta id, and this is the way to name an element which has no identifier, for example a rule or a reaction which was written without one.

The report searches the element with that meta id in the model and links it.

<span id="sbaseref"></span>**sBaseRef**

A port which names a submodel of its model can reach through it with a [nested reference](sbaseref.md), so that the port stands for an element buried inside that submodel. The chain may be of any length, one link per submodel it passes.

The report shows the chain in the inspector of the port and links the element at its end.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [Model](model.md): the container of everything a model is made of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.4.3 (Smith et al. 2015, J Integr Bioinform 12(2):268).
