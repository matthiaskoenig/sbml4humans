# External model definition

A model of another SBML file which this document can instantiate.

An external model definition makes a model of another file available under an identifier of this document, so that a [submodel](submodel.md) can instantiate it. It is a declaration, not a use: it says where the file is and which model inside it is meant. The identifier belongs to this document and is not the identifier of the model it points at.

The report shows the external model definitions of a document next to its models. It does not open the file they point at, so what it shows is the declaration, not the model behind it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| source | `anyURI` | <span id="source"></span>the location of the SBML file which holds the model | [Section 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| model ref | `SIdRef` | <span id="model-ref"></span>the identifier of the model inside the referenced file | [Section 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [Model](model.md): the container of everything a model is made of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition (comp)](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.3.2 (Smith et al. 2013, Version 1 Release 3).
