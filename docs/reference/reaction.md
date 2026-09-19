# Reaction

A process which changes the quantities of species.

A reaction is any process which changes how much of a species there is: a chemical conversion, a transport across a membrane, a binding, a degradation. It names the species it consumes as reactants and the species it produces as products, each with a stoichiometry, and it may name modifiers which influence its speed without being changed. How fast it runs is given by its [kinetic law](kineticlaw.md), which is optional: without one the speed of the reaction is undefined.

The report shows the equation of a reaction, its kinetic law and the units of that law, and lists its reactants, products and modifiers with links to the species.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [reversible](#reversible) | [`boolean`](datatypes.md#boolean) | required | whether the reaction can also run backwards | [core 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [fast](#fast) | [`boolean`](datatypes.md#boolean) | optional | whether the reaction was declared to be much faster than the others | [core 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [compartment](#compartment) | [`SIdRef`](datatypes.md#sidref) | optional | the compartment in which the reaction takes place | [core 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfReactants](#listofreactants) | [`list`](datatypes.md#list) | optional | the species the reaction consumes, with their stoichiometry | [core 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfProducts](#listofproducts) | [`list`](datatypes.md#list) | optional | the species the reaction produces, with their stoichiometry | [core 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfModifiers](#listofmodifiers) | [`list`](datatypes.md#list) | optional | the species which influence the reaction without being consumed | [core 4.11.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [kineticLaw](#kineticlaw) | [`KineticLaw`](kineticlaw.md) | optional | the formula which gives the speed of the reaction | [core 4.11.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [fbc](#fbc) | `ReactionFbc` | - | the flux bounds and the gene association which fbc adds to a reaction | [fbc v3 3.8](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:lowerFluxBound](#fbc-lowerfluxbound) | [`SIdRef`](datatypes.md#sidref) | - | the parameter which holds the smallest flux the reaction may carry | [fbc v3 3.8](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:upperFluxBound](#fbc-upperfluxbound) | [`SIdRef`](datatypes.md#sidref) | - | the parameter which holds the largest flux the reaction may carry | [fbc v3 3.8](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |
| [fbc:geneProductAssociation](#fbc-geneproductassociation) | [`GeneProductAssociation`](geneproductassociation.md) | - | the genes under which the reaction can run | [fbc v3 3.9](https://identifiers.org/combine.specifications/sbml.level-3.version-1.fbc.version-3.release-1) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="reversible"></span>**reversible**

The flag says whether the process can proceed in both directions. It does not change the equations of a simulation, it is an assertion which structural analyses such as elementary mode analysis rely on, and which says that the rate of an irreversible reaction never becomes negative.

The report shows the flag as a mark in the column "reversible", a check for a reversible reaction and a cross for an irreversible one, and writes the equation with a double arrow for a reversible reaction. Level 1 and Level 2 make a reaction reversible unless the file says otherwise, so a reaction of those levels which does not write the flag is shown as reversible; Level 3 has no default.

<span id="fast"></span>**fast**

In SBML Level 2 and in Level 3 Version 1 a fast reaction was one which reaches a quasi steady state immediately. The attribute was removed in Level 3 Version 2, where the speed of every reaction is given by its kinetic law alone.

The report shows the flag for the models which still carry it, so that a model of an older level can be read as it was written. Level 1 and Level 2 from Version 2 on make a reaction slow unless the file says otherwise, so a reaction of those levels which does not write the flag is shown with the cross of `false`; Level 2 Version 1 gave the flag no default, and a reaction of that version which does not write it is shown with the dash of an attribute which is not set.

Default: the attribute exists up to Level 3 Version 1, where it is required, and Level 3 Version 2 removed it: every reaction is equivalent to one with false.

- `21152` (warning): The value of the 'fast' attribute should be 'false', as the attribute has been deprecated.

<span id="compartment"></span>**compartment**

The compartment is optional and has no effect on the equations of the model; it helps a reader, a visualisation or a tool which checks a rate law to know where the process happens.

The report links the compartment in the column "compartment" and in the inspector.

- `21107` (error): The value of the attribute 'compartment' in a &lt;reaction&gt; object is optional, but if present, must be the identifier of an existing Compartment object defined in the model.

<span id="listofreactants"></span>**listOfReactants**

Every reactant is a [species reference](speciesreference.md) which names a species of the model and how much of it one reaction event consumes. A reaction has at least one reactant or one product.

The report lists the reactants in the inspector of the reaction, with a link to every species, and writes them on the left of the equation.

Default: the reaction consumes nothing and must then have a product.

- `21101` (error): A &lt;reaction&gt; definition must contain at least one &lt;speciesReference&gt;, either in its &lt;listOfReactants&gt; or its &lt;listOfProducts&gt;. A reaction without any reactant or product species is not permitted, regardless of whether the reaction has any modifier species.
- `21104` (error): The list of reactants (&lt;listOfReactants&gt;) and list of products (&lt;listOfProducts&gt;) in a &lt;reaction&gt; can only contain &lt;speciesReference&gt; elements.

<span id="listofproducts"></span>**listOfProducts**

Every product is a [species reference](speciesreference.md) which names a species of the model and how much of it one reaction event produces.

The report lists the products in the inspector of the reaction and writes them on the right of the equation.

Default: the reaction produces nothing and must then have a reactant.

- `21101` (error): A &lt;reaction&gt; definition must contain at least one &lt;speciesReference&gt;, either in its &lt;listOfReactants&gt; or its &lt;listOfProducts&gt;. A reaction without any reactant or product species is not permitted, regardless of whether the reaction has any modifier species.
- `21104` (error): The list of reactants (&lt;listOfReactants&gt;) and list of products (&lt;listOfProducts&gt;) in a &lt;reaction&gt; can only contain &lt;speciesReference&gt; elements.

<span id="listofmodifiers"></span>**listOfModifiers**

A modifier is a [modifier species reference](modifierspeciesreference.md): a catalyst, an inhibitor or an activator which appears in the kinetic law but is neither created nor destroyed. Modifiers have no stoichiometry.

The report lists the modifiers in the inspector of the reaction, with a link to every species; they are not part of the equation, which shows what a reaction consumes and produces.

- `21105` (error): The list of modifiers (&lt;listOfModifiers&gt;) in a &lt;reaction&gt; can only contain &lt;modifierSpeciesReference&gt; elements.

<span id="kineticlaw"></span>**kineticLaw**

The [kinetic law](kineticlaw.md) holds the rate formula of the reaction and the local parameters it uses. It is optional, and a reaction without one has no defined speed, which different simulators treat differently.

The report shows the rendered formula in the column "kinetic law" and the whole kinetic law in the inspector of the reaction.

Default: the speed of the reaction is undefined.

<span id="fbc"></span>**fbc**

The fbc package extends a reaction with the two parameters which bound its flux and with the gene product association which says under which genes it can run. Together with the [objective](objective.md) of the model they are what a flux balance analysis needs.

The report shows the bounds, the association and the gene products it names in the inspector of a reaction of a model which uses fbc.

<span id="fbc-lowerfluxbound"></span>**fbc:lowerFluxBound**

The bound is not a number but the identifier of a [parameter](parameter.md) of the model, so that many reactions can share one bound and a scenario is changed in one place. A model which sets `strict` of the fbc package has to give every reaction both bounds, and every bound has to be a constant parameter with a value which is neither missing nor infinite in the direction which would remove the bound; without `strict` a bound may be computed during a simulation.

The report links the parameter in the inspector of the reaction.

<span id="fbc-upperfluxbound"></span>**fbc:upperFluxBound**

Like the lower bound it names a [parameter](parameter.md) of the model, and a reaction whose flux is fixed points with both attributes at the same parameter. The package defines SBO terms which mark a parameter as a flux bound.

The report links the parameter in the inspector of the reaction.

<span id="fbc-geneproductassociation"></span>**fbc:geneProductAssociation**

The [association](geneproductassociation.md) is a tree of the operators `and` and `or` over the [gene products](geneproduct.md) of the model: `and` for the subunits of one complex, `or` for the isoenzymes which can do the same job. `((b3670 and b3671) or (b0077 and b0078))` is such an expression, and it is what a knockout analysis evaluates when it removes a gene.

The report shows the tree in the inspector of the reaction, one line per branch, and links every gene product it names.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [kineticLaw](#kineticlaw-2) | [`Math`](datatypes.md#math) | the rate formula of the reaction's kinetic law, rendered |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units the report derives for the rate formula of the kinetic law |
| [equation](#equation) | [`string`](datatypes.md#string) | the reaction written as a chemical equation |

<span id="kineticlaw-2"></span>**kineticLaw**

The table of reactions shows the formula of the [kinetic law](kineticlaw.md) directly in its own column "kinetic law", so a reader does not have to open the reaction to see how fast it runs. It is the same formula the inspector renders under "math" of the kinetic law; a reaction without a kinetic law shows a dash.

<span id="derived-units"></span>**derived units**

The report derives the units of the [kinetic law](kineticlaw.md)'s formula from the units of the quantities it uses, and shows them in the column "derived units" of the table of reactions, next to the formula. They should be the extent units of the model divided by its time units, which is the check a modeller wants to make on a rate law.

<span id="equation"></span>**equation**

The report builds the equation from the reactants and the products of the reaction, with a single or a double arrow according to the flag "reversible". A stoichiometry of one is left out, a stoichiometry of minus one becomes a minus in front of the species, and a stoichiometry which is no number, because a rule or an initial assignment sets it, is replaced by the identifier of the species reference, or by a question mark when it has none. The modifiers are not part of it, they are shown in the inspector. It is the fastest way to see what a reaction does without opening it.

The equation is a column of the table of reactions and a row of the inspector.

## Validation rules

- `10707` (warning): The value of the 'sboTerm' attribute on a &lt;reaction&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to an occurring entity representation defined in SBO (i.e., terms derived from SBO:0000231, "occurring entity representation").
- `21102` (error): The order of subelements within &lt;reaction&gt; must be the following: &lt;listOfReactants&gt; (optional), &lt;listOfProducts&gt; (optional), &lt;listOfModifiers&gt; (optional), &lt;kineticLaw&gt;.
- `21103` (error): The following containers are all optional in a &lt;reaction&gt;, but if any is present, it must not be empty: &lt;listOfReactants&gt;, &lt;listOfProducts&gt;, &lt;listOfModifiers&gt;, &lt;kineticLaw&gt;.
- `21106` (error): A &lt;reaction&gt; object may contain at most one of each of the following elements: &lt;listOfReactants&gt;, &lt;listOfProducts&gt;, &lt;listOfModifiers&gt;, and &lt;kineticLaw&gt;.
- `21110` (error): A &lt;reaction&gt; object must have the required attributes 'id' and 'reversible', and may have the optional attributes 'metaid', 'sboTerm', 'name' and 'compartment'. For SBML Level 3 Version 1 documents only, 'fast' is additionally required. No other attributes from the SBML Level 3 Core namespace are permitted on a Reaction object.

## Related elements

- [Species](species.md): a pool of a chemical entity in a compartment
- [SpeciesReference](speciesreference.md): the participation of a species in a reaction as a reactant or a product
- [ModifierSpeciesReference](modifierspeciesreference.md): the participation of a species in a reaction as a modifier
- [KineticLaw](kineticlaw.md): the formula which gives the speed of a reaction
- [Compartment](compartment.md): a bounded space in which species are located

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
