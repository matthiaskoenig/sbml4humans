# External model definition

A model of another SBML file which this document can instantiate.

An external model definition makes a model of another file available under an identifier of this document, so that a [submodel](submodel.md) can instantiate it. It is a declaration, not a use: it says where the file is and which model inside it is meant. The identifier belongs to this document and is not the identifier of the model it points at.

The report shows the external model definitions of a document next to its models. It does not open the file they point at, so what it shows is the declaration, not the model behind it.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [source](#source) | `anyURI` | the location of the SBML file which holds the model | [comp 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [model ref](#model-ref) | `SIdRef` | the identifier of the model inside the referenced file | [comp 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [md5](#md5) | `string` | the checksum of the document at the source | [comp 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="source"></span>**source**

The source is a URI, which may be a URL, a URN or a location relative to this document. The whole file at that location is referenced and it has to be an SBML Level 3 Version 1 document; earlier levels and versions are not supported by the package.

The report shows the source in the inspector of the external model definition.

<span id="model-ref"></span>**model ref**

The reference names a model or another external model definition of the document at the source. When it is not set, the main model of that file is meant, which is the case a model without an identifier leaves. Following a chain of external model definitions has to end at a model.

The report shows the reference in the inspector; it is not resolved to an element, the referenced file is not read.

<span id="md5"></span>**md5**

The checksum is optional and is the md5 sum of the whole file at the source, as it was when the model was written. It is how a reader tells whether the file they reach is the file the composed model was built against, which matters when the source is a URL that somebody else maintains.

The report shows the checksum in the inspector of the external model definition; it does not fetch the file and cannot check it.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [Model](model.md): the container of everything a model is made of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.3.2 (Smith et al. 2015, J Integr Bioinform 12(2):268).
