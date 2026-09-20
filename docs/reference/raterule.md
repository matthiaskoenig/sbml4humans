# RateRule

A formula which gives the rate of change of an element.

A rate rule states the derivative of a variable with respect to time: `dx/dt = f(W)`. It is how a model describes a change which is not the result of reactions, for example the growth of a compartment or an ordinary differential equation written directly. The element it changes must not be constant, and a species which is produced or consumed by a reaction may only have a rate rule when it is a boundary condition.

The report shows the variable, the rendered formula and the units the formula produces, which are the units of the variable per unit of time.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [variable](#variable) | [`SIdRef`](datatypes.md#sidref) | required | the element whose rate of change the rule gives | [core 4.9.4](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula which computes the rate of change | [core 4.9.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="variable"></span>**variable**

The variable names the compartment, species, species reference or parameter which changes. It must not be constant, and no other rule may determine the same variable.

The report links the named element in the column "variable" and in the inspector.

- `10304` (error): The value of the 'variable' field in all &lt;assignmentRule&gt; and &lt;rateRule&gt; definitions must be unique across the set of all such rule definitions in a model.
- `20902` (error): The value of a &lt;rateRule&gt;'s 'variable' must be the identifier of an existing &lt;compartment&gt;, &lt;species&gt;, globally-defined &lt;parameter&gt;, or (in Level 3) &lt;speciesReference&gt;, or (in Level 3 Version 2), any identifier in the SId namespace of the model belonging to an element defined by an SBML Level 3 package as having with mathematical meaning.
- `20904` (error): Any &lt;compartment&gt;, &lt;species&gt;, &lt;parameter&gt;, or (in Level 3) &lt;speciesReference&gt; whose identifier is the value of a 'variable' attribute in an &lt;rateRule&gt;, must have a value of 'false' for 'constant'.
- `20911` (error): The value of a &lt;rateRule&gt; or &lt;assignmentRule&gt;'s 'variable' attribute must not be the identifier of a &lt;compartment&gt; with a 'spatialDimensions' value of 0.

<span id="math"></span>**math**

The math is an arbitrary expression which returns a number. Its units should be the units of the variable divided by the time units of the model.

The report renders the formula in the column "math" and in the inspector.

Default: how the rule behaves mathematically stays undefined.

- `20907` (error): Every AssignmentRule, RateRule and AlgebraicRule object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the formula as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the formula from the units of the quantities it uses. They should be the units of the variable per unit of time of the model.

## Validation rules

- `10705` (warning): The value of the 'sboTerm' attribute on a rule is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a mathematical expression (i.e., terms derived from SBO:0000064, "mathematical expression"). Note: This applies to Algebraic Rules in addition to Rate and Assignment Rules.
- `20909` (error): A RateRule object must have the required attribute 'variable' and may have the optional attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on a RateRule object.
- `20912` (error): There must not be circular dependencies in the combined set of &lt;rateRule&gt; and &lt;kineticLaw&gt; objects in the model. Each of these constructs has the effect of assigning a value to the time derivative of one or more identifiers (i.e., the identifier given in the attribute 'variable' in the &lt;rateRule&gt;, and the identifier of any &lt;species&gt; referenced by a &lt;speciesReference&gt; in the same &lt;reaction&gt; as the &lt;kineticLaw&gt;). Each of these constructs computes the value using a mathematical formula. The formula used to calculate the time derivative of a given identifier cannot make reference to a second identifier whose own definition depends directly or indirectly on a 'rateOf' 'csymbol' for the first identifier.

## Related elements

- [AssignmentRule](assignmentrule.md): a formula which holds at every moment of the simulation
- [AlgebraicRule](algebraicrule.md): an equation which has to hold at every moment of the simulation
- [Reaction](reaction.md): a process which changes the quantities of species

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.9.4 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
