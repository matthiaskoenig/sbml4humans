# User defined constraint

A constraint over a combination of fluxes and parameters, added in Version 3.

The bounds of a [reaction](reaction.md) constrain one flux at a time, and the stoichiometry of the network constrains the fluxes which share a species. A user defined constraint is everything else a modeller knows: that two reactions run at a fixed ratio, that a set of reactions shares a budget, or that a flux is coupled to a parameter which a simulation changes.

It is a sum of its [components](userdefinedconstraintcomponent.md), each of which weighs one model variable, and the sum has to stay between the values of the two [parameters](parameter.md) it names as its bounds.

The report shows the user defined constraints of a model in a section of their own, with the table of their components.

## Attributes

| attribute | type | meaning | specification |
| --- | --- | --- | --- |
| [lower bound](#lower-bound) | `SIdRef` | the parameter which holds the smallest value the constraint may take | [fbc v3 3.14](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [upper bound](#upper-bound) | `SIdRef` | the parameter which holds the largest value the constraint may take | [fbc v3 3.14](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [components](#components) | `list` | the weighted variables the constraint is the sum of | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="lower-bound"></span>**lower bound**

The attribute is required and names a [parameter](parameter.md) of the model, the way the lower flux bound of a reaction does, so that a scenario is changed in one place. A constraint whose two bounds name the same parameter is an equality.

<span id="upper-bound"></span>**upper bound**

The attribute is required and names a [parameter](parameter.md) of the model. Together with the lower bound it reads `lowerBound <= sum of the components <= upperBound`.

<span id="components"></span>**components**

A constraint which is defined has at least one [component](userdefinedconstraintcomponent.md). The report shows them as a table of the variable, the coefficient and the type of every term, with a link to each of them.

## Related elements

- [User defined constraint component](userdefinedconstraintcomponent.md): one weighted variable of a user defined constraint
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.14 (Olivier and Bergmann, COMBINE specification).
