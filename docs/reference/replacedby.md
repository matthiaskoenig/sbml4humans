# ReplacedBy

The element of a submodel which takes the place of the element carrying it.

A replaced by turns a replacement around: the element which carries it disappears and the element of the [submodel](submodel.md) it names stays, so that every reference to the element of the containing model points into the submodel afterwards. It is how a model declares a placeholder which one of its parts fills in.

An element carries at most one replaced by, and it names the element which replaces it the same four ways a [replaced element](replacedelement.md) does, with a [nested reference](sbaseref.md) for an element which sits deeper.

The report shows the replacement in the inspector of the element, links the submodel and the element inside it, and shows the replacement as an element of its own.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [submodelRef](#submodelref) | `SIdRef` | the submodel which holds the replacing element | [comp 3.6.4](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [portRef](#portref) | `PortSIdRef` | the port of the submodel whose element takes the place of this element | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | `SIdRef` | the element which replaces this element, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | `UnitSIdRef` | the unit definition which replaces this unit definition | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | `IDREF` | the element which replaces this element, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref) | `SBaseRef` | the reference which reaches into a submodel of the named submodel | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="submodelref"></span>**submodelRef**

The reference names a [submodel](submodel.md) of the model which carries the replacement. It is required, and the other references are resolved in the model that submodel instantiates.

<span id="portref"></span>**portRef**

The replacement names a [port](port.md) of the model the submodel instantiates, and the element behind that port is the one which stays.

<span id="idref"></span>**idRef**

The identifier is resolved in the model the named submodel instantiates.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own. The units which SBML reserves cannot replace anything.

<span id="metaidref"></span>**metaIdRef**

This is the way to name a replacing element which carries no identifier of its own.

<span id="sbaseref"></span>**sBaseRef**

A replacement which names a submodel of the instantiated model carries a [nested reference](sbaseref.md) which names the element inside it, so that an element of a sub-submodel takes the place of this element.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [ReplacedElement](replacedelement.md): an element of a submodel which the element carrying it takes the place of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.6.4 (Smith et al. 2015, J Integr Bioinform 12(2):268).
