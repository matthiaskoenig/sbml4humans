# SBaseRef

A link of a chain which reaches into a submodel of a submodel.

A reference names one element of a model in one of four ways: by [port](port.md), by identifier, by unit identifier or by meta id, and exactly one of the four is set.

A [port](port.md), a [deletion](deletion.md), a [replaced element](replacedelement.md) and a [replaced by](replacedby.md) are references themselves. Where one of them has to reach an element which sits deeper than the submodel it names, it carries a reference of this class, which names an element of the model that submodel instantiates, and that reference may carry the next one. The chain is how a model reaches an element of a sub-submodel which no port of its own exposes.

The report shows the chain in the inspector of the element which starts it and resolves it to the element at its end.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [portRef](#portref) | `PortSIdRef` | - | the port of the model which this link of the chain names | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [idRef](#idref) | [`SIdRef`](datatypes.md#sidref) | - | the element which this link of the chain names, by its identifier | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [unitRef](#unitref) | [`UnitSIdRef`](datatypes.md#unitsidref) | - | the unit definition which this link of the chain names | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [metaIdRef](#metaidref) | `IDREF` | - | the element which this link of the chain names, by its meta id | [comp 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [sBaseRef](#sbaseref-2) | [`SBaseRef`](sbaseref.md) | - | the next link of the chain, one submodel deeper | [comp 3.7.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="portref"></span>**portRef**

The reference names a [port](port.md) of the model the submodel above it instantiates. Port identifiers are a namespace of their own, so a port may carry the identifier of an element of the same model without naming it.

<span id="idref"></span>**idRef**

The reference names an element of the model the submodel above it instantiates. When that element is a [submodel](submodel.md) again, the next link of the chain reaches into it.

<span id="unitref"></span>**unitRef**

Unit identifiers live in a namespace of their own, so naming a [unit definition](unitdefinition.md) needs an attribute of its own. The units which SBML reserves cannot be named here: they can neither be replaced nor deleted.

<span id="metaidref"></span>**metaIdRef**

Every element of a file may carry a meta id, and this is the way to name an element which has no identifier of its own, for example a rule or a reaction written without one.

<span id="sbaseref-2"></span>**sBaseRef**

A reference which names a [submodel](submodel.md) carries the reference which names the element inside it. There is no limit to the depth of the chain.

## Related elements

- [Port](port.md): an element of the model which other models are meant to connect to
- [Deletion](deletion.md): an element which is removed from a submodel before it is instantiated
- [ReplacedElement](replacedelement.md): an element of a submodel which the element carrying it takes the place of
- [ReplacedBy](replacedby.md): the element of a submodel which takes the place of the element carrying it
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.7 (Smith et al. 2015, J Integr Bioinform 12(2):268).
