# Submodel

The instantiation of another model inside this model.

A submodel is a use of a model definition: everything the referenced model contains becomes part of the composed model. Before it is instantiated, the referenced model may be modified in two ways. Deletions remove the elements which do not belong in the new context, for example an initial assignment which the containing model provides itself, and conversion factors rescale the time and the reaction extent of the submodel to the scales of the containing model.

Loops are not allowed: a model may not instantiate itself, directly or through a chain of submodels.

The report links the model a submodel instantiates, shows its two conversion factors and lists its deletions.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [model](#model) | `SIdRef` | the model which this submodel instantiates | [comp 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [time conversion factor](#time-conversion-factor) | `SIdRef` | the parameter which converts the time of the submodel into the time of this model | [comp 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [extent conversion factor](#extent-conversion-factor) | `SIdRef` | the parameter which converts the reaction extent of the submodel into the extent of this model | [comp 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| [deletions](#deletions) | `list` | the elements which are removed from the model before it is instantiated | [comp 3.5.3](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="model"></span>**model**

The reference names a [model](model.md) definition or an [external model definition](externalmodeldefinition.md) of the same document. It is required, a submodel without it has nothing to instantiate.

The report links the model in the column "model" and in the inspector of the submodel.

<span id="time-conversion-factor"></span>**time conversion factor**

The factor is the identifier of a constant, dimensionless [parameter](parameter.md) of the containing model. One unit of time in the submodel multiplied by the factor is one unit of time here, and every reference to time of the submodel is converted with it: the time and delay symbols, the delays of events, the rate rules and the kinetic laws. The factors of nested submodels multiply.

The report links the parameter in the column "time conversion factor" and in the inspector.

<span id="extent-conversion-factor"></span>**extent conversion factor**

The extent of a reaction is how much of it has happened, which is what a kinetic law is the rate of. Like the time conversion factor this attribute names a constant, dimensionless [parameter](parameter.md) of the containing model, so that a submodel written in millimole can be used in a model written in mole.

The report links the parameter in the column "extent conversion factor" and in the inspector.

<span id="deletions"></span>**deletions**

A deletion names one element of the referenced model which is not wanted in this context. The removal is conceptual: the submodel is everything of the referenced model minus the deleted elements, and minus what depends on them. Every deletion names its element the same four ways a [port](port.md) does, by port, identifier, unit identifier or meta id.

The report shows the number of deletions in the column "deletions" and the four references of every deletion in the inspector.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [External model definition](externalmodeldefinition.md): a model of another SBML file which this document can instantiate
- [Port](port.md): an element of the model which other models are meant to connect to
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.5 (Smith et al. 2015, J Integr Bioinform 12(2):268).
