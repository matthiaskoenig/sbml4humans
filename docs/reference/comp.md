# Hierarchical Model Composition (comp)

The package which builds a model out of other models.

A package of SBML Level 3 adds elements and attributes for a domain which not every model needs, and declares itself in the file so that a reader knows whether it has to understand them; this is what makes Level 3 modular instead of one growing language ([Keating et al. 2020](https://doi.org/10.15252/msb.20199110)).

The comp package adds composition. A [submodel](submodel.md) instantiates another model, a [port](port.md) marks the elements through which other models are meant to interact with it, a deletion removes what does not belong in the new context, and a replacement glues an element of the containing model onto an element of a submodel. The models which are instantiated are either model definitions of the same file or [external model definitions](externalmodeldefinition.md) pointing at another file.

The report shows the model definitions of a document next to its main model, the submodels and the ports of a model as sections of their own, and the replacements of an element in its inspector.

## Related elements

- [External model definition](externalmodeldefinition.md): a model of another SBML file which this document can instantiate
- [Submodel](submodel.md): the instantiation of another model inside this model
- [Port](port.md): an element of the model which other models are meant to connect to
- [Model](model.md): the container of everything a model is made of

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/) (Smith et al. 2015, J Integr Bioinform 12(2):268).
