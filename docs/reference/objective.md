# Objective

The function a flux balance analysis maximises or minimises.

An objective is a direction, "maximize" or "minimize", together with a weighted sum of reaction fluxes, its flux objectives. It is what turns a network with bounds into a solvable optimisation problem: the fluxes are chosen within the bounds of the reactions so that this sum becomes extremal.

The classical objective of a genome scale model is a single term of coefficient one on the biomass reaction, which asks for the flux distribution with the fastest growth.

The report shows the objectives of a model in a section of their own and lists the reaction and the coefficient of every flux objective, with a link to the reaction.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [type](#type) | `FbcType` | whether the objective is maximised or minimised | [fbc 3.6](https://sbml.org/specifications/sbml-level-3/version-1/fbc/sbml-fbc-version-2-release-1.pdf) |
| [flux objectives](#flux-objectives) | `list` | the reactions of the objective with their coefficient | [fbc 3.7](https://sbml.org/specifications/sbml-level-3/version-1/fbc/sbml-fbc-version-2-release-1.pdf) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="type"></span>**type**

The type is the sense of the optimality constraint and is either `maximize` or `minimize`. It is required, an objective without it is not defined.

The report shows the type in the column "type" and in the inspector.

<span id="flux-objectives"></span>**flux objectives**

A flux objective is one term of the objective function: the [reaction](reaction.md) whose flux is meant and the coefficient the flux is weighted with. An objective which is defined has at least one of them.

The report shows the number of flux objectives in the column "flux objectives" and the table of the reactions with their coefficients in the inspector, with a link to every reaction.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 2 Release 1](https://sbml.org/specifications/sbml-level-3/version-1/fbc/sbml-fbc-version-2-release-1.pdf), Section 3.6 (Olivier and Bergmann 2018, J Integr Bioinform 15(1):20170082).
