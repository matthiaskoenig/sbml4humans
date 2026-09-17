# Objective

The function a flux balance analysis maximises or minimises.

An objective is a direction, "maximize" or "minimize", together with a weighted sum of reaction fluxes, its flux objectives. It is what turns a network with bounds into a solvable optimisation problem: the fluxes are chosen within the bounds of the reactions so that this sum becomes extremal.

The classical objective of a genome scale model is a single term of coefficient one on the biomass reaction, which asks for the flux distribution with the fastest growth.

The report shows the objectives of a model in a section of their own and lists the reaction and the coefficient of every flux objective, with a link to the reaction.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| type | `FbcType` | <span id="type"></span>whether the objective is maximised or minimised | [Section 3.6](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |
| flux objectives | `list` | <span id="flux-objectives"></span>the reactions of the objective with their coefficient | [Section 3.7](https://sbml.org/documents/specifications/level-3/version-1/fbc/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints (fbc)](https://sbml.org/documents/specifications/level-3/version-1/fbc/), Section 3.6 (Olivier et al. 2026, Version 3 Release 1).
