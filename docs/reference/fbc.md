# Flux Balance Constraints (fbc)

The package which describes a constraint based model.

A constraint based model does not integrate rate laws over time. It assumes a steady state and chooses the fluxes of the reactions so that an objective function becomes extremal while every flux stays within its bounds, which is what flux balance analysis does with a genome scale reconstruction.

The fbc package holds what such a model needs beyond the core: the lower and the upper flux bound of a [reaction](reaction.md), the [objectives](objective.md) with their flux objectives, the [gene products](geneproduct.md) and the association which relates them to a reaction, and the chemical formula and the charge of a [species](species.md). Its three versions write part of it differently: Version 1 states a bound as a [flux bound](fluxbound.md) of its own, Version 2 makes the two bounds attributes of the reaction which name parameters and adds the gene products, and Version 3 adds the [user defined constraints](userdefinedconstraint.md) over several fluxes and the key value pairs which annotate an element.

The report shows the gene products, the objectives, the flux bounds of Version 1 and the user defined constraints of Version 3 as sections of a model of their own, and the fbc attributes of a species and of a reaction in their inspector.

## Validation rules

- `2010101` (error): To conform to Version 1 of the Flux Balance Constraints package specification for SBML Level 3, an SBML document must declare the use of the following XML Namespace: 'http://www.sbml.org/sbml/level3/version1/fbc/version1'
- `2010102` (error): Wherever they appear in an SBML document, elements and attributes from the Flux Balance Constraints package must be declared either implicitly or explicitly to be in the XML namespace 'http://www.sbml.org/sbml/level3/version1/fbc/version1'
- `2020101` (error): In all SBML documents using the Flux Balance Constraints package, the SBML object must include a value for the attribute 'fbc:required'.
- `2020102` (error): The value of attribute 'fbc:required' on the SBML object must be of the data type Boolean.
- `2020103` (error): The value of attribute 'fbc:required' on the SBML object must be set to 'false'.

## Related elements

- [GeneProduct](geneproduct.md): a gene or one of its products which the reactions of the model depend on
- [GeneProductAssociation](geneproductassociation.md): the genes a reaction needs, as the tree of operators over them
- [Objective](objective.md): the function a flux balance analysis maximises or minimises
- [FluxBound](fluxbound.md): a constraint on the flux of a reaction, as fbc Version 1 writes it
- [UserDefinedConstraint](userdefinedconstraint.md): a constraint over a combination of fluxes and parameters, added in Version 3
- [Species](species.md): a pool of a chemical entity in a compartment
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) (Olivier and Bergmann, COMBINE specification).
