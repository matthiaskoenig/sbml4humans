# Objective

The function a flux balance analysis maximises or minimises.

An objective is a direction, "maximize" or "minimize", together with a weighted sum of reaction fluxes, its flux objectives. It is what turns a network with bounds into a solvable optimisation problem: the fluxes are chosen within the bounds of the reactions so that this sum becomes extremal.

The classical objective of a genome scale model is a single term of coefficient one on the biomass reaction, which asks for the flux distribution with the fastest growth.

The report shows the objectives of a model in a section of their own and lists the reaction and the coefficient of every flux objective, with a link to the reaction.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [type](#type) | [`FbcType`](datatypes.md#fbctype) | required | whether the objective is maximised or minimised | [fbc v3 3.6](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [listOfFluxObjectives](#listoffluxobjectives) | [`list`](datatypes.md#list) | required | the reactions of the objective with their coefficient | [fbc v3 3.7](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="type"></span>**type**

The type is the sense of the optimality constraint and is either `maximize` or `minimize`. It is required, an objective without it is not defined.

The report shows the type in the column "type" and in the inspector.

- `2020505` (error): The attribute 'fbc:type' on an &lt;objective&gt; must be of the data type FbcType and thus its value must be one of 'minimize' or 'maximize.

<span id="listoffluxobjectives"></span>**listOfFluxObjectives**

A flux objective is one term of the objective function: the [reaction](reaction.md) whose flux is meant and the coefficient the flux is weighted with. An objective which is defined has at least one of them.

The report shows the number of flux objectives in the column "flux objectives" and the table of the reactions with their coefficients in the inspector, with a link to every reaction.

- `2020506` (error): An &lt;objective&gt; object must have one and only one instance of the &lt;listOfFluxObjectives&gt; object.
- `2020507` (error): The &lt;listOfFluxObjectives&gt; subobject within an &lt;objective&gt; object must not be empty.
- `2020508` (error): Apart from the general notes and annotation subobjects permitted on all SBML objects, a &lt;listOfFluxObjectives&gt; container object may only contain &lt;fluxObjective&gt; objects.

## Validation rules

- `2010301` (error): (Extends validation rule #10301 in the SBML Level 3 Version 1 Core specification.) Within a &lt;model&gt; object the values of the attributes id and fbc:id on every instance of the following classes of objects must be unique across the set of all id and fbc:id attribute values of all such objects in a model: the model itself, plus all contained &lt;functionDefinition&gt;, &lt;compartment&gt;, &lt;species&gt;, &lt;reaction&gt;, &lt;speciesReference&gt;, &lt;modifierSpeciesReference&gt;, &lt;event&gt;, and &lt;parameter&gt; objects, plus the &lt;fluxBound&gt;, &lt;objective&gt;, &lt;fluxObjective&gt;, &lt;geneProduct&gt; and &lt;geneProductAssociation&gt; objects defined by the Flux Balance Constraints package.
- `2020501` (error): An &lt;objective&gt; object may have the optional SBML Level 3 Core attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on an &lt;objective&gt;.
- `2020502` (error): An &lt;objective&gt; object may have the optional SBML Level 3 Core subobjects for notes and annotations. No other elements from the SBML Level 3 Core namespace are permitted on an &lt;objective&gt;.
- `2020503` (error): An &lt;objective&gt; object must have the required attributes 'fbc:id' and 'fbc:type' and may have the optional attribute 'fbc:name'. No other attributes from the SBML Level 3 Flux Balance Constraints namespace are permitted on an &lt;objective&gt; object.
- `2020506` (error): An &lt;objective&gt; object must have one and only one instance of the &lt;listOfFluxObjectives&gt; object.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Flux Balance Constraints (fbc)](fbc.md): the package which describes a constraint based model

## Specification

[SBML Level 3 Package: Flux Balance Constraints, Version 3 Release 1](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1), Section 3.6 (Olivier and Bergmann, COMBINE specification).
