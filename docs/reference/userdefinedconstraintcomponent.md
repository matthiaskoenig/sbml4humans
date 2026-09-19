# UserDefinedConstraintComponent

One weighted variable of a user defined constraint.

A component is one term of the sum a [user defined constraint](userdefinedconstraint.md) bounds: the model variable it is about, the [parameter](parameter.md) which holds the number the variable is multiplied with, and whether the variable enters the sum linearly or quadratically.

The variable is either a [reaction](reaction.md), whose flux is meant, or a parameter which is not constant, which is how a constraint reaches a quantity the network does not carry.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [variable](#variable) | [`SIdRef`](datatypes.md#sidref) | required | the reaction or the parameter this term of the constraint weighs | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [variable2](#variable2) | [`SIdRef`](datatypes.md#sidref) | optional | the second variable of a mixed quadratic term | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [coefficient](#coefficient) | [`SIdRef`](datatypes.md#sidref) | required | the parameter which holds the number the variable is multiplied with | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [variableType](#variabletype) | [`FbcVariableType`](datatypes.md#fbcvariabletype) | required | whether the variable enters the constraint linearly or quadratically | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="variable"></span>**variable**

The attribute is required and names either a [reaction](reaction.md), in which case the term is about its flux, or a [parameter](parameter.md) which is not constant. The report links the element it names.

- `2021305` (error): The value of the attribute 'fbc:variable' of an &lt;userDefinedConstraintComponent&gt; object must be the identifier of an existing &lt;reaction&gt; or &lt;parameter&gt; object defined in the enclosing &lt;model&gt; object.

<span id="variable2"></span>**variable2**

A quadratic component which names a second variable weighs the product of the two, `coefficient * v1 * v2`, instead of the square of the first. It is optional and empty in a linear component.

Default: a quadratic component is the square of its first variable.

- `2021308` (error): The value of the attribute 'fbc:variable2' of an &lt;userDefinedConstraintComponent&gt; object must be the identifier of an existing &lt;reaction&gt; or &lt;parameter&gt; object defined in the enclosing &lt;model&gt; object.

<span id="coefficient"></span>**coefficient**

Unlike the coefficient of a [flux objective](fluxobjective.md), which is a number written into the file, the coefficient of a component is the identifier of a [parameter](parameter.md), so that the weights of a constraint can be changed in one place. In a strict model that parameter has to be constant and its value finite.

- `2021304` (error): The value of the attribute 'fbc:coefficient' of an &lt;userDefinedConstraintComponent&gt; object must be the identifier of an existing &lt;parameter&gt; object defined in the enclosing &lt;model&gt; object.

<span id="variabletype"></span>**variableType**

The type is `linear` or `quadratic`, as in a [flux objective](fluxobjective.md): a quadratic component squares its variable, or multiplies it by the second variable where it names one. It is required.

- `2021306` (error): The value of the attribute 'fbc:variableType' of an &lt;userDefinedConstraintComponent&gt; object must conform to the syntax of SBML data type 'FbcVariableType' and may only take on the allowed values of 'FbcVariableType' defined in SBML; that is, the value must be one of the following: 'linear' or 'quadratic'.

## Validation rules

- `2021301` (error): An &lt;userDefinedConstraintComponent&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespaces are permitted on an &lt;userDefinedConstraintComponent&gt;.
- `2021302` (error): An &lt;userDefinedConstraintComponent&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on an &lt;userDefinedConstraintComponent&gt;.
- `2021303` (error): An &lt;userDefinedConstraintComponent&gt; object must have the required attributes 'fbc:coefficient', 'fbc:variable' and 'fbc:variableType', and may have the optional attributes 'fbc:id', 'fbc:name' and 'fbc:variable2'. No other attributes from the SBML Level 3 Flux Balance Constraints namespaces are permitted on an &lt;userDefinedConstraintComponent&gt; object.

## Related elements

- [UserDefinedConstraint](userdefinedconstraint.md): a constraint over a combination of fluxes and parameters, added in Version 3
- [Reaction](reaction.md): a process which changes the quantities of species
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.15 (Olivier and Bergmann, COMBINE specification).
