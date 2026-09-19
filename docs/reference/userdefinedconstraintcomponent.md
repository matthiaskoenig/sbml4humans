# UserDefinedConstraintComponent

One weighted variable of a user defined constraint.

A component is one term of the sum a [user defined constraint](userdefinedconstraint.md) bounds: the model variable it is about, the [parameter](parameter.md) which holds the number the variable is multiplied with, and whether the variable enters the sum linearly or quadratically.

The variable is either a [reaction](reaction.md), whose flux is meant, or a parameter which is not constant, which is how a constraint reaches a quantity the network does not carry.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [variable](#variable) | [`SIdRef`](datatypes.md#sidref) | - | the reaction or the parameter this term of the constraint weighs | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [variable2](#variable2) | [`SIdRef`](datatypes.md#sidref) | - | the second variable of a mixed quadratic term | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [coefficient](#coefficient) | [`SIdRef`](datatypes.md#sidref) | - | the parameter which holds the number the variable is multiplied with | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [variableType](#variabletype) | `FbcVariableType` | - | whether the variable enters the constraint linearly or quadratically | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="variable"></span>**variable**

The attribute is required and names either a [reaction](reaction.md), in which case the term is about its flux, or a [parameter](parameter.md) which is not constant. The report links the element it names.

<span id="variable2"></span>**variable2**

A quadratic component which names a second variable weighs the product of the two, `coefficient * v1 * v2`, instead of the square of the first. It is optional and empty in a linear component.

<span id="coefficient"></span>**coefficient**

Unlike the coefficient of a [flux objective](fluxobjective.md), which is a number written into the file, the coefficient of a component is the identifier of a [parameter](parameter.md), so that the weights of a constraint can be changed in one place. In a strict model that parameter has to be constant and its value finite.

<span id="variabletype"></span>**variableType**

The type is `linear` or `quadratic`, as in a [flux objective](fluxobjective.md): a quadratic component squares its variable, or multiplies it by the second variable where it names one. It is required.

## Related elements

- [UserDefinedConstraint](userdefinedconstraint.md): a constraint over a combination of fluxes and parameters, added in Version 3
- [Reaction](reaction.md): a process which changes the quantities of species
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.15 (Olivier and Bergmann, COMBINE specification).
