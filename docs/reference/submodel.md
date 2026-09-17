# Submodel

The instantiation of another model inside this model.

A submodel is a use of a model definition: everything the referenced model contains becomes part of the composed model. Before it is instantiated, the referenced model may be modified in two ways. Deletions remove the elements which do not belong in the new context, for example an initial assignment which the containing model provides itself, and conversion factors rescale the time and the reaction extent of the submodel to the scales of the containing model.

Loops are not allowed: a model may not instantiate itself, directly or through a chain of submodels.

The report links the model a submodel instantiates, shows its two conversion factors and lists its deletions.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| model ref | `SIdRef` | <span id="model-ref"></span>the model which this submodel instantiates | [Section 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| time conversion factor | `SIdRef` | <span id="time-conversion-factor"></span>the parameter which converts the time of the submodel into the time of this model | [Section 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| extent conversion factor | `SIdRef` | <span id="extent-conversion-factor"></span>the parameter which converts the reaction extent of the submodel into the extent of this model | [Section 3.5.1](https://sbml.org/documents/specifications/level-3/version-1/comp/) |
| deletions | `list` | <span id="deletions"></span>the elements which are removed from the model before it is instantiated | [Section 3.5.3](https://sbml.org/documents/specifications/level-3/version-1/comp/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Model](model.md): the container of everything a model is made of
- [External model definition](externalmodeldefinition.md): a model of another SBML file which this document can instantiate
- [Port](port.md): an element of the model which other models are meant to connect to
- [Hierarchical Model Composition (comp)](comp.md): the package which builds a model out of other models

## Specification

[SBML Level 3 Package: Hierarchical Model Composition (comp)](https://sbml.org/documents/specifications/level-3/version-1/comp/), Section 3.5 (Smith et al. 2013, Version 1 Release 3).
