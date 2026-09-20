# UserDefinedConstraint

A constraint over a combination of fluxes and parameters, added in Version 3.

The bounds of a [reaction](reaction.md) constrain one flux at a time, and the stoichiometry of the network constrains the fluxes which share a species. A user defined constraint is everything else a modeller knows: that two reactions run at a fixed ratio, that a set of reactions shares a budget, or that a flux is coupled to a parameter which a simulation changes.

It is a sum of its [components](userdefinedconstraintcomponent.md), each of which weighs one model variable, and the sum has to stay between the values of the two [parameters](parameter.md) it names as its bounds.

The report shows the user defined constraints of a model in a section of their own, with the table of their components.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [lowerBound](#lowerbound) | [`SIdRef`](datatypes.md#sidref) | required | the parameter which holds the smallest value the constraint may take | [fbc v3 3.14](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [upperBound](#upperbound) | [`SIdRef`](datatypes.md#sidref) | required | the parameter which holds the largest value the constraint may take | [fbc v3 3.14](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [listOfUserDefinedConstraintComponents](#listofuserdefinedconstraintcomponents) | [`list`](datatypes.md#list) | required | the weighted variables the constraint is the sum of | [fbc v3 3.15](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="lowerbound"></span>**lowerBound**

The attribute is required and names a [parameter](parameter.md) of the model, the way the lower flux bound of a reaction does, so that a scenario is changed in one place. A constraint whose two bounds name the same parameter is an equality.

- `2021405` (error): The value of the attribute 'fbc:lowerBound' of an &lt;userDefinedConstraint&gt; object must be the identifier of an existing &lt;parameter&gt; object defined in the enclosing &lt;model&gt; object.

<span id="upperbound"></span>**upperBound**

The attribute is required and names a [parameter](parameter.md) of the model. Together with the lower bound it reads `lowerBound <= sum of the components <= upperBound`.

- `2021406` (error): The value of the attribute 'fbc:upperBound' of an &lt;userDefinedConstraint&gt; object must be the identifier of an existing &lt;parameter&gt; object defined in the enclosing &lt;model&gt; object.

<span id="listofuserdefinedconstraintcomponents"></span>**listOfUserDefinedConstraintComponents**

A constraint which is defined has at least one [component](userdefinedconstraintcomponent.md). The report shows them as a table of the variable, the coefficient and the type of every term, with a link to each of them.

- `2021404` (error): An &lt;userDefinedConstraint&gt; object must contain one and only one instance of the &lt;listOfUserDefinedConstraintComponents&gt; element. No other elements from the SBML Level 3 Flux Balance Constraints namespaces are permitted on an &lt;userDefinedConstraint&gt; object.
- `2021408` (error): Apart from the general notes and annotations subobjects permitted on all SBML objects, a &lt;listOfUserDefinedConstraintComponents&gt; container object may only contain &lt;userDefinedConstraintComponent&gt; objects.

## Validation rules

- `2021401` (error): An &lt;userDefinedConstraint&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespaces are permitted on an &lt;userDefinedConstraint&gt;.
- `2021402` (error): An &lt;userDefinedConstraint&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespaces are permitted on an &lt;userDefinedConstraint&gt;.
- `2021403` (error): An &lt;userDefinedConstraint&gt; object must have the required attributes 'fbc:lowerBound' and 'fbc:upperBound', and may have the optional attributes 'fbc:id' and 'fbc:name'. No other attributes from the SBML Level 3 Flux Balance Constraints namespaces are permitted on an &lt;userDefinedConstraint&gt; object.
- `2021404` (error): An &lt;userDefinedConstraint&gt; object must contain one and only one instance of the &lt;listOfUserDefinedConstraintComponents&gt; element. No other elements from the SBML Level 3 Flux Balance Constraints namespaces are permitted on an &lt;userDefinedConstraint&gt; object.

## Related elements

- [UserDefinedConstraintComponent](userdefinedconstraintcomponent.md): one weighted variable of a user defined constraint
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Reaction](reaction.md): a process which changes the quantities of species
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.14 (Olivier and Bergmann, COMBINE specification).
