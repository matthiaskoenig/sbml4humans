# Replaced by

The element of a submodel which takes the place of the element carrying it.

A replaced by turns a replacement around: the element which carries it disappears and the element of the [submodel](submodel.md) it names stays, so that every reference to the element of the containing model points into the submodel afterwards. It is how a model declares a placeholder which one of its parts fills in.

An element carries at most one replaced by, and it names the element which replaces it the same four ways a [replaced element](replacedelement.md) does, with a [nested reference](sbaseref.md) for an element which sits deeper.

The report shows the replacement in the inspector of the element, links the submodel and the element inside it, and shows the replacement as an element of its own.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [submodel](#submodel) | `SIdRef` | the submodel which holds the replacing element | [comp 3.6.4](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [port ref](#port-ref) | `PortSIdRef` | the port of the submodel whose element takes the place of this element | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [id ref](#id-ref) | `SIdRef` | the element which replaces this element, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unit ref](#unit-ref) | `UnitSIdRef` | the unit definition which replaces this unit definition | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [meta id ref](#meta-id-ref) | `IDREF` | the element which replaces this element, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [nested reference](#nested-reference) | `SBaseRef` | the reference which reaches into a submodel of the named submodel | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="submodel"></span>**submodel**

The reference names a [submodel](submodel.md) of the model which carries the replacement. It is required, and the other references are resolved in the model that submodel instantiates.

<span id="port-ref"></span>**port ref**

The replacement names a [port](port.md) of the model the submodel instantiates, and the element behind that port is the one which stays.

<span id="id-ref"></span>**id ref**

The identifier is resolved in the model the named submodel instantiates.

<span id="unit-ref"></span>**unit ref**

Unit identifiers live in a namespace of their own. The units which SBML reserves cannot replace anything.

<span id="meta-id-ref"></span>**meta id ref**

This is the way to name a replacing element which carries no identifier of its own.

<span id="nested-reference"></span>**nested reference**

A replacement which names a submodel of the instantiated model carries a [nested reference](sbaseref.md) which names the element inside it, so that an element of a sub-submodel takes the place of this element.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [Replaced element](replacedelement.md): an element of a submodel which the element carrying it takes the place of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.6.4 (Smith et al. 2015, J Integr Bioinform 12(2):268).
