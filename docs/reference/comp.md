# Hierarchical Model Composition (comp)

The package which builds a model out of other models.

A package of SBML Level 3 adds elements and attributes for a domain which not every model needs, and declares itself in the file so that a reader knows whether it has to understand them; this is what makes Level 3 modular instead of one growing language ([Keating et al. 2020](https://doi.org/10.15252/msb.20199110)).

The comp package adds composition. A [submodel](submodel.md) instantiates another model, a [port](port.md) marks the elements through which other models are meant to interact with it, a deletion removes what does not belong in the new context, and a replacement glues an element of the containing model onto an element of a submodel. The models which are instantiated are either model definitions of the same file or [external model definitions](externalmodeldefinition.md) pointing at another file.

The report shows the model definitions of a document next to its main model, the submodels and the ports of a model as sections of their own, and the replacements of an element in its inspector.

## Validation rules

- `1010101` (error): To conform to Version 1 of the Hierarchical Model Composition package specification for SBML Level 3, an SBML document must declare the use of the following XML Namespace: 'http://www.sbml.org/sbml/level3/version1/comp/version1'
- `1010102` (error): Wherever they appear in an SBML document, elements and attributes from the Hierarchical Model Composition package must be declared either implicitly or explicitly to be in the XML namespace 'http://www.sbml.org/sbml/level3/version1/comp/version1'
- `1020201` (error): In all SBML documents using the HierarchicalModel Composition package, the SBML object must include a value for the attribute 'comp:required' attribute.
- `1020202` (error): The value of attribute 'comp:required' on the SBML object must be of the data type Boolean.
- `1020205` (error): There may be at most one instance of the &lt;listOfModelDefinitions&gt; within an SBML object that uses the SBML Level 3 Hierarchical Model Composition package.
- `1020206` (error): The various 'ListOf' subobjects within an SBML object are optional, but if present, these container objects must not be empty. Specifically, if any of the following classes of objects is present within the SBML object, it must not be empty: &lt;listOfModelDefinitions&gt; and &lt;listOfExternalModelDefinitions&gt;.
- `1020207` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfModelDefinitions&gt; container may only contain &lt;modelDefinition&gt; objects.
- `1020208` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfExternalModelDefinitions&gt; container may only contain &lt;externalModelDefinition&gt; objects.
- `1020211` (error): There may be at most one instance of the &lt;listOfExternalModelDefinitions&gt; within an SBML object that uses the SBML Level 3 Hierarchical Model Composition package.
- `1020212` (error): The value of attribute 'comp:required' on the SBML object must be set to 'true'.

## Related elements

- [ExternalModelDefinition](externalmodeldefinition.md): a model of another SBML file which this document can instantiate
- [Submodel](submodel.md): the instantiation of another model inside this model
- [Port](port.md): an element of the model which other models are meant to connect to
- [Model](model.md): the container of everything a model is made of

## Specification

[SBML Level 3 Package: Hierarchical Model Composition, Version 1 Release 3](https://sbml.org/documents/specifications/level-3/version-1/comp/) (Smith et al. 2015, J Integr Bioinform 12(2):268).
