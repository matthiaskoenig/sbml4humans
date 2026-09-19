# ExternalModelDefinition

A model of another SBML file which this document can instantiate.

An external model definition makes a model of another file available under an identifier of this document, so that a [submodel](submodel.md) can instantiate it. It is a declaration, not a use: it says where the file is and which model inside it is meant. The identifier belongs to this document and is not the identifier of the model it points at.

The report shows the external model definitions of a document next to its models, and it follows one to the model it names where it was given the document at its source: another entry of the same COMBINE archive, or a file next to a model which was read from a directory, as the examples are. The references of the [submodels](submodel.md) which instantiate it, the [replacements](replacedelement.md), the [deletions](deletion.md) and the [ports](port.md), then end at the element they name inside that model. The report never fetches a document, and the [status](externalmodeldefinition.md) of the definition says how far it could be followed.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [source](#source) | [`anyURI`](datatypes.md#anyuri) | required | the location of the SBML file which holds the model | [comp 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [modelRef](#modelref) | [`SIdRef`](datatypes.md#sidref) | optional | the identifier of the model inside the referenced file | [comp 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [md5](#md5) | [`string`](datatypes.md#string) | optional | the checksum of the document at the source | [comp 3.3.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="source"></span>**source**

The source is a URI, which may be a URL, a URN or a location relative to this document. The whole file at that location is referenced and it has to be an SBML Level 3 Version 1 document; earlier levels and versions are not supported by the package.

The report shows the source in the inspector of the external model definition. A relative source is resolved against the location of the document which names it, inside the COMBINE archive both are entries of. A source with a scheme, such as a URL, is shown and never fetched.

- `1020304` (error): The value of the 'comp:source' attribute on an &lt;externalModelDefinition&gt; object must reference an SBML Level 3 document.
- `1020307` (error): The value of a 'comp:source' attribute on an &lt;externalModelDefinition&gt; object must always conform to the syntax of the XML Schema 1.0 data type 'anyURI'.

<span id="modelref"></span>**modelRef**

The reference names a model or another external model definition of the document at the source. When it is not set, the main model of that file is meant, which is the case a model without an identifier leaves. Following a chain of external model definitions has to end at a model.

The report shows the reference in the inspector and follows it where it has the document at the source, through a chain of external model definitions to the model at its end.

Default: the main model of the document at the source.

- `1020305` (error): The value of the 'comp:modelRef' attribute on an &lt;externalModelDefinition&gt; object must be the value of an id attribute on a &lt;model&gt;, &lt;modelDefinition&gt;, or &lt;externalModelDefinition&gt; object in the SBML document referenced by the 'comp:source' attribute.
- `1020308` (error): The value of a comp:modelRef attribute on an &lt;externalModelDefinition&gt; object must always conform to the syntax of the SBML data type SId.
- `1020310` (error): An &lt;externalModelDefinition&gt; object must not reference an &lt;externalModelDefinition&gt; in a different SBML document that, in turn, refers back to the original &lt;externalModelDefinition object, whether directly or indirectly through a chain of &lt;externalModelDefinition&gt; objects.

<span id="md5"></span>**md5**

The checksum is optional and is the md5 sum of the whole file at the source, as it was when the model was written. It is how a reader tells whether the file they reach is the file the composed model was built against, which matters when the source is a URL that somebody else maintains.

The report shows the checksum in the inspector of the external model definition and compares it with the document it has at the source. It does not fetch a file, so the checksum of a remote source is not checked.

Default: nothing checks that the document at the source is the one the definition was written against.

- `1020306` (warning): The value of the 'comp:md5' attribute, if present on an &lt;externalModelDefinition&gt; object, should match the calculated MD5 checksum of the SBML document referenced by the 'comp:source' attribute.
- `1020309` (error): The value of a comp:md5 attribute on an &lt;externalModelDefinition&gt; object must always conform to the syntax of type string.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [status](#status) | [`string`](datatypes.md#string) | how far the report could follow the external model definition |
| [document](#document) | [`string`](datatypes.md#string) | the entry of the archive which the source names |
| [model](#model) | [`string`](datatypes.md#string) | the model the external model definition names |
| [md5 check](#md5-check) | [`boolean`](datatypes.md#boolean) | whether the document at the source has the checksum the definition states |

<span id="status"></span>**status**

The report reads the documents it was given and never fetches one, so whether it can follow an external model definition depends on where its source points. The status is one of six:

- `resolved`: the document at the source is part of the report and holds the model. The references into the [submodels](submodel.md) of this definition end at the element they name.
- `remoteSource`: the source is a URI with a scheme, such as a URL. The report does not fetch it, so that the time of a report does not depend on another server and a model cannot make the server request an address.
- `notFound`: the source is a relative location and the report has no document there. This is the status of every external model definition of an SBML file which is uploaded on its own; a COMBINE archive which holds both files resolves it.
- `notSbml`: there is a file at the source, but it holds no SBML model the report could read.
- `modelNotFound`: the document at the source has no model with the identifier the model reference names, or no model at all.
- `circular`: the model reference names an external model definition of the other document, and following the chain comes back to where it started.

Unless the status is `resolved`, the references into the submodels end at the submodel.

<span id="document"></span>**document**

The location of the entry in the [manifest](concepts.md#manifest) of the COMBINE archive, as soon as there is an entry at the source, whether or not the model could be found in it. For a chain of external model definitions it is the entry of the last document which was found.

The inspector links the entry when the report has a model of it.

<span id="model"></span>**model**

The [model](model.md) or model definition of the other document which the model reference names, the main model of that document where no model reference is set, and the model at the end of the chain where the reference names another external model definition.

The inspector links the model, which opens the report of the other entry, and the link is shown under "References" of the definition and under "Referenced by" of the model.

<span id="md5-check"></span>**md5 check**

The report computes the md5 sum of the document it has at the source and compares it with the md5 of the definition. It is not set when the definition states no checksum or when the report has no document to compare with.

A checksum which does not match says that the file is not the one the composed model was written against. The report states the mismatch and still follows the definition, because the document in the archive is the one the model will be run with.

## Validation rules

- `1010302` (error): The values of the attributes 'id' and 'comp:id' on every instance of all &lt;model&gt;, &lt;modelDefinition&gt;, and &lt;externalModelDefinition&gt; objects must be unique across the set of all 'id' and 'comp:id' attribute values of such objects in the SBML document to which they belong.
- `1020301` (error): An &lt;externalModelDefinition&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on an &lt;externalModelDefinition&gt; object.
- `1020302` (error): An &lt;externalModelDefinition&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotation. No other subobjects from the SBML Level 3 Core namespace or the Hierarchical Model Composition namespace are permitted on an &lt;externalModelDefinition&gt; object.
- `1020303` (error): An &lt;externalModelDefinition&gt; object must have the attributes 'comp:id' and 'comp:source', and may have the optional attributes 'comp:name', 'comp:modelRef', and 'comp:md5'. No other attributes from the Hierarchical Model Composition namespace are permitted on an &lt;externalModelDefinition&gt; object.

## Related elements

- [Submodel](submodel.md): the instantiation of another model inside this model
- [Model](model.md): the container of everything a model is made of
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.3.2 (Smith et al. 2015, J Integr Bioinform 12(2):268).
