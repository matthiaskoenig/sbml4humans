# Submodel

The instantiation of another model inside this model.

A submodel is a use of a model definition: everything the referenced model contains becomes part of the composed model. Before it is instantiated, the referenced model may be modified in two ways. Deletions remove the elements which do not belong in the new context, for example an initial assignment which the containing model provides itself, and conversion factors rescale the time and the reaction extent of the submodel to the scales of the containing model.

Loops are not allowed: a model may not instantiate itself, directly or through a chain of submodels.

The report links the model a submodel instantiates, shows its two conversion factors and lists its deletions.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [modelRef](#modelref) | [`SIdRef`](datatypes.md#sidref) | required | the model which this submodel instantiates | [comp 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [timeConversionFactor](#timeconversionfactor) | [`SIdRef`](datatypes.md#sidref) | optional | the parameter which converts the time of the submodel into the time of this model | [comp 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [extentConversionFactor](#extentconversionfactor) | [`SIdRef`](datatypes.md#sidref) | optional | the parameter which converts the reaction extent of the submodel into the extent of this model | [comp 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [listOfDeletions](#listofdeletions) | [`list`](datatypes.md#list) | optional | the elements which are removed from the model before it is instantiated | [comp 3.5.2](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="modelref"></span>**modelRef**

The reference names a [model](model.md) definition or an [external model definition](externalmodeldefinition.md) of the same document. It is required, a submodel without it has nothing to instantiate.

The report links the model in the column "model" and in the inspector of the submodel.

- `1020608` (error): The value of a 'comp:modelRef' attribute on a &lt;submodel&gt; object must always conform to the syntax of the SBML data type SId.
- `1020615` (error): The value of a 'comp:modelRef' attribute on a &lt;submodel&gt; must be the identifier of a &lt;model&gt;, &lt;modelDefinition&gt;, or &lt;externalModelDefinition&gt; object in the same SBML object as the &lt;submodel&gt;.
- `1020616` (error): A &lt;model&gt; or &lt;modelDefinition&gt; object must not contain a &lt;submodel&gt; which references that model object itself. That is, the value of a 'comp:modelRef' attribute on a &lt;submodel&gt; must not be the value of the parent &lt;model&gt; or &lt;modelDefinition&gt;'s 'id' attribute.
- `1020617` (error): A &lt;model&gt; object must not contain a &lt;submodel&gt; which references that &lt;model&gt; indirectly. That is, the 'comp:modelRef' attribute of a &lt;submodel&gt; may not point to the 'id' of a &lt;model&gt; containing a &lt;submodel&gt; object that references the original &lt;model&gt; directly or indirectly through a chain of &lt;model&gt;/&lt;submodel&gt; pairs.

<span id="timeconversionfactor"></span>**timeConversionFactor**

The factor is the identifier of a constant, dimensionless [parameter](parameter.md) of the containing model. One unit of time in the submodel multiplied by the factor is one unit of time here, and every reference to time of the submodel is converted with it: the time and delay symbols, the delays of events, the rate rules and the kinetic laws. The factors of nested submodels multiply.

The report links the parameter in the column "time conversion factor" and in the inspector.

Default: one unit of time in the submodel is one unit of time in this model.

- `1020613` (error): The value of a 'comp:timeConversionFactor' attribute on a &lt;submodel&gt; object must always conform to the syntax of the SBML data type SId.
- `1020622` (error): The value of a 'comp:timeConversionFactor' attribute on a given &lt;submodel&gt; object must be the identifier of a &lt;parameter&gt; object defined in the same Model containing the &lt;submodel&gt;.

<span id="extentconversionfactor"></span>**extentConversionFactor**

The extent of a reaction is how much of it has happened, which is what a kinetic law is the rate of. Like the time conversion factor this attribute names a constant, dimensionless [parameter](parameter.md) of the containing model, so that a submodel written in millimole can be used in a model written in mole.

The report links the parameter in the column "extent conversion factor" and in the inspector.

Default: one unit of reaction extent in the submodel is one unit of extent in this model.

- `1020614` (error): The value of a 'comp:extentConversionFactor' attribute on a &lt;submodel&gt; object must always conform to the syntax of the SBML data type SId.
- `1020623` (error): The value of a 'comp:extentConversionFactor' attribute on a given &lt;submodel&gt; object must be the identifier of a &lt;parameter&gt; object defined in the same Model containing the &lt;submodel&gt;.

<span id="listofdeletions"></span>**listOfDeletions**

A deletion names one element of the referenced model which is not wanted in this context. The removal is conceptual: the submodel is everything of the referenced model minus the deleted elements, and minus what depends on them. Every deletion names its element the same four ways a [reference](sbaseref.md) of the package does, by port, identifier, unit identifier or meta id.

The report shows the number of deletions in the column "deletions" and the four references of every deletion in the inspector.

Default: the referenced model is instantiated whole.

- `1020603` (error): There may be at most one &lt;listOfDeletions&gt; container object within a &lt;submodel&gt; object.
- `1020604` (error): A &lt;listOfDeletions&gt; container object within a &lt;submodel&gt; object is optional, but if present, must not be empty.
- `1020605` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfDeletions&gt; container object may only contain &lt;deletion&gt; objects.

## Validation rules

- `1010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; or &lt;modelDefinition&gt; object, the values of the attributes id and comp:id on every instance of the following classes of objects must be unique across the set of all id and comp:id attribute values of all such objects in a model: the model itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;submodel&gt; and &lt;deletion&gt; objects defined by the Hierarchical Model Composition package, plus any objects defined by any other package with 'package:id' attributes defined as falling in the 'SId' namespace.
- `1020601` (error): A &lt;submodel&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a &lt;submodel&gt; object.
- `1020602` (error): A &lt;submodel&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespace are permitted on a &lt;submodel&gt; object.
- `1020607` (error): A &lt;submodel&gt; object must have the attributes 'comp:id' and 'comp:modelRef' because they are required, and may also have the optional attributes 'comp:name', 'comp:timeConversionFactor, and/or 'comp:extentConversionFactor'. No other attributes from the Hierarchical Model Composition namespace are permitted on a &lt;submodel&gt; object.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [ExternalModelDefinition](externalmodeldefinition.md): a model of another SBML file which this document can instantiate
- [Port](port.md): an element of the model which other models are meant to connect to
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.5 (Smith et al. 2015, J Integr Bioinform 12(2):268).
