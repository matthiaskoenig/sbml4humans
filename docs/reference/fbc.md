# Flux Balance Constraints (fbc)

The package which describes a constraint based model.

A constraint based model does not integrate rate laws over time. It assumes a steady state and chooses the fluxes of the reactions so that an objective function becomes extremal while every flux stays within its bounds, which is what flux balance analysis does with a genome scale reconstruction.

The fbc package holds what such a model needs beyond the core: the lower and the upper flux bound of a [reaction](reaction.md), the [objectives](objective.md) with their flux objectives, the [gene products](geneproduct.md) and the association which relates them to a reaction, and the chemical formula and the charge of a [species](species.md).

The report shows the gene products and the objectives of a model as sections of their own and the fbc attributes of a species and of a reaction in their inspector.

## Related elements

- [Gene product](geneproduct.md): a gene or one of its products which the reactions of the model depend on
- [Objective](objective.md): the function a flux balance analysis maximises or minimises
- [Species](species.md): a pool of a chemical entity in a compartment
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 2 Release 1](https://sbml.org/documents/specifications/level-3/version-1/fbc/) (Olivier and Bergmann 2018, J Integr Bioinform 15(1):20170082).
