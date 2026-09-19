# FluxObjective

One term of an objective: a reaction weighted by a coefficient.

A flux objective names the [reaction](reaction.md) whose flux enters the objective function and the number the flux is multiplied with. An [objective](objective.md) is the sum of its flux objectives, so a genome scale model usually carries one term of coefficient one on its biomass reaction.

It is an element of the report and not a row of its objective, because the specification derives it from `SBase`: it may carry an identifier, a name, an SBO term, notes and annotations, and the reference to its reaction starts here, not at the objective around it.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [reaction](#reaction) | [`SIdRef`](datatypes.md#sidref) | required | the reaction whose flux this term of the objective weighs | [fbc v3 3.7](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [reaction2](#reaction2) | [`SIdRef`](datatypes.md#sidref) | optional | the second reaction of a mixed quadratic term, from Version 3 on | [fbc v3 3.7](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [coefficient](#coefficient) | [`double`](datatypes.md#double) | required | the number the flux of the reaction is multiplied with | [fbc v3 3.7](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [variableType](#variabletype) | [`FbcVariableType`](datatypes.md#fbcvariabletype) | required | whether the flux enters the objective linearly or quadratically | [fbc v3 3.7](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="reaction"></span>**reaction**

The attribute is required and names a [reaction](reaction.md) of the model. The report links it, and the inspector of that reaction shows the flux objective under "referenced by", which is how the reactions an analysis optimises are found.

- `2020605` (error): The value of the attribute 'fbc:reaction' of a &lt;fluxObjective&gt; object must conform to the syntax of the SBML data type 'SIdRef'.
- `2020606` (error): The value of the attribute 'fbc:reaction' of a &lt;fluxObjective&gt; object must be the identifier of an existing &lt;reaction&gt; object defined in the enclosing &lt;model&gt; object.

<span id="reaction2"></span>**reaction2**

A quadratic flux objective which names a second [reaction](reaction.md) weighs the product of the two fluxes, `coefficient * J1 * J2`, instead of the square of one. The attribute exists from Version 3 of the package on and is empty in every earlier document.

The report links the reaction next to the first one.

Default: a quadratic term is the square of the flux of the first reaction.

- `2020610` (error): The value of the attribute 'fbc:reaction2' of a &lt;fluxObjective&gt; object must conform to the syntax of the SBML data type 'SIdRef'.
- `2020611` (error): The value of the attribute 'fbc:reaction2' of a &lt;fluxObjective&gt; object must be the identifier of an existing &lt;reaction&gt; object defined in the enclosing &lt;model&gt; object.

<span id="coefficient"></span>**coefficient**

The coefficient is a signed number and carries no units, since the term takes the units of the flux, extent per time. A negative coefficient turns a term of a maximisation into one which is pushed down, which is how one objective can trade growth against the uptake of a substrate.

In a strict model the coefficient has to be a finite number. The report shows it next to the reaction.

- `2020607` (error): The value of the attribute 'fbc:coefficient' of a &lt;fluxObjective&gt; object must conform to the syntax of the SBML data type 'double'.
- `2020608` (error): When the value of the &lt;model&gt; 'fbc:strict' attribute is true, the value of the attribute 'fbc:coefficient' of a &lt;fluxObjective&gt; object must not be set to 'NaN', 'INF' or '-INF'.

<span id="variabletype"></span>**variableType**

The type is `linear`, the classical case in which the flux appears as it is, or `quadratic`, in which it appears squared or multiplied by the flux of the second reaction. Without it a quadratic term reads like a linear one, and `Minimize: 1 R1 + [4 R2^2]/2` and `Minimize: 1 R1 + 4 R2` cannot be told apart.

The attribute is required from Version 3 of the package on and does not exist before it, so a Version 1 or Version 2 document leaves it empty and every term of its objectives is linear.

- `2020609` (error): The value of the attribute 'fbc:variableType' of a &lt;fluxObjective&gt; object must conform to the syntax of SBML data type 'FbcVariableType' and may only take on the allowed values of 'FbcVariableType' defined in SBML; that is, the value must be one of the following: 'linear' or 'quadratic'.

## Validation rules

- `2010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; object the values of the attributes id and fbc:id on every instance of the following classes of objects must be unique across the set of all id and fbc:id attribute values of all such objects in a model: the model itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;fluxBound&gt;, &lt;objective&gt;, &lt;fluxObjective&gt;, &lt;geneProduct&gt; and &lt;geneProductAssociation&gt; objects defined by the Flux Balance Constraints package.
- `2020601` (error): A &lt;fluxObjective&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a &lt;fluxObjective&gt;.
- `2020602` (error): A &lt;fluxObjective&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespace are permitted on a &lt;fluxObjective&gt;.
- `2020603` (error): A &lt;fluxObjective&gt; object must have the required attributes 'fbc:reaction' and 'fbc:coefficient', and may have the optional attributes 'fbc:id' and 'fbc:name'. No other attributes from the SBML Level 3 Flux Balance Constraints namespace are permitted on a &lt;fluxObjective&gt; object.

## Related elements

- [Objective](objective.md): the function a flux balance analysis maximises or minimises
- [Reaction](reaction.md): a process which changes the quantities of species
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.7 (Olivier and Bergmann, COMBINE specification).
