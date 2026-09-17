# Port

An element of the model which other models are meant to connect to.

A port gives a name to one element of the model and declares it as an intended point of interaction, so that a model which includes this one connects to the port instead of reaching into the model. Port identifiers live in a namespace of their own, which is why a port may carry the same identifier as an element of the model.

Exactly one of the four references of a port is set, and each of them names the element in a different way. The use of ports is advisory in this version of the package, nothing enforces it.

The report shows which element a port names, links it, and lists the ports of a model in a section of their own.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| port ref | `PortSIdRef` | <span id="port-ref"></span>the port which this reference names | [Section 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| id ref | `SIdRef` | <span id="id-ref"></span>the element which this port names, by its identifier | [Section 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| unit ref | `UnitSIdRef` | <span id="unit-ref"></span>the unit definition which this port names | [Section 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| meta id ref | `IDREF` | <span id="meta-id-ref"></span>the element which this port names, by its meta id | [Section 3.7.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [Model](model.md): the container of everything a model is made of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition (comp)](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.4.3 (Smith et al. 2013, Version 1 Release 3).
