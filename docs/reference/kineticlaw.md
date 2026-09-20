# KineticLaw

The formula which gives the speed of a reaction.

The kinetic law of a reaction holds the formula which computes how fast the process runs, and the local parameters which only that formula uses. The formula may use the global elements of the model, its own local parameters and the species which the reaction declares as reactants, products or modifiers. Its units are the extent units of the model divided by its time units.

The report shows the rendered formula, the units it derives for it and the table of the local parameters.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the rate formula of the reaction | [core 4.11.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [listOfLocalParameters](#listoflocalparameters) | [`list`](datatypes.md#list) | optional | the parameters which only this kinetic law uses | [core 4.11.6](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="math"></span>**math**

The math is an expression which returns a number, the rate of change of the extent of the reaction. A kinetic law without a formula leaves the speed of the reaction undefined.

The report renders the formula in the column "kinetic law" of the reactions and in the inspector.

Default: the speed of the reaction stays undefined.

- `21121` (error): All species referenced in the &lt;kineticLaw&gt; formula of a given reaction must first be declared using &lt;speciesReference&gt; or &lt;modifierSpeciesReference&gt;. More formally, if a &lt;species&gt; identifier appears in a &lt;ci&gt; element of a &lt;reaction&gt;'s &lt;kineticLaw&gt; formula, that same identifier must also appear in at least one &lt;speciesReference&gt; or &lt;modifierSpeciesReference&gt; in the &lt;reaction&gt; definition.
- `21130` (error): A KineticLaw object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

<span id="listoflocalparameters"></span>**listOfLocalParameters**

The list holds the [local parameters](localparameter.md) of the kinetic law. A local parameter hides a global parameter of the same identifier inside the formula, which is worth knowing when a value looks surprising.

The report shows the local parameters as a table in the inspector of the kinetic law and of the reaction.

Default: the formula uses the global elements of the model alone.

- `21123` (error): If present, the &lt;listOfParameters&gt; in a &lt;kineticLaw&gt; must not be an empty list.
- `21127` (error): A KineticLaw object may contain at most one ListOfLocalParameters container object.
- `21128` (error): Apart from the general Notes and Annotation subobjects permitted on all SBML components, a ListOfLocalParameters container object may only contain LocalParameter objects.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the rate formula as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the formula from the units of the quantities it uses. They should be the extent units of the model divided by its time units, which is the check a modeller wants to make on a rate law.

## Validation rules

- `10709` (warning): The value of the 'sboTerm' attribute on a &lt;kineticLaw&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring rate law defined in SBO (i.e., terms derived from SBO:0000001, "rate law").
- `20906` (error): There must not be circular dependencies in the combined set of &lt;initialAssignment&gt;, &lt;assignmentRule&gt; and &lt;kineticLaw&gt; definitions in a model. Each of these constructs has the effect of assigning a value to an identifier (i.e. the identifier given in the field 'symbol' in &lt;initialAssignment&gt;, the field 'variable' in &lt;assignmentRule&gt;, and the field 'id' on the &lt;kineticLaw&gt;'s enclosing &lt;reaction&gt;). Each of these constructs computes the value using a mathematical formula. The formula for a given identifier cannot make reference to a second identifier whose own definition depends directly or indirectly on the first identifier.
- `21122` (error): The order of subelements within &lt;kineticLaw&gt; must be the following: &lt;math&gt;, &lt;listOfParameters&gt;. The &lt;listOfParameters&gt; is optional, but if present, must follow &lt;math&gt;.
- `21132` (error): A KineticLaw object may have the optional attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a KineticLaw object.

## Related elements

- [Reaction](reaction.md): a process which changes the quantities of species
- [LocalParameter](localparameter.md): a named value which only one kinetic law uses
- [Parameter](parameter.md): a named value which the mathematics of the model can use

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.11.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
