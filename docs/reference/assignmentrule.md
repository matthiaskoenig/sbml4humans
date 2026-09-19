# AssignmentRule

A formula which holds at every moment of the simulation.

An assignment rule states that a variable of the model equals an expression, at all times, and not only at the start: `x = f(V)`. It is the way to define a quantity which follows from others, for example a total concentration or a saturation. The element it assigns to must not be constant, and no other rule may assign to the same element.

The report shows the variable, the rendered formula and the units the formula produces.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [variable](#variable) | [`SIdRef`](datatypes.md#sidref) | required | the element the rule assigns to | [core 4.9.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula which computes the value of the variable | [core 4.9.1](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="variable"></span>**variable**

The variable names the compartment, species, species reference or parameter whose value the rule determines. It must not be constant, and a model may not contain a second rule for the same variable.

The report links the named element in the column "variable" and in the inspector.

- `10304` (error): The value of the 'variable' field in all &lt;assignmentRule&gt; and &lt;rateRule&gt; definitions must be unique across the set of all such rule definitions in a model.
- `20901` (error): The value of an &lt;assignmentRule&gt;'s 'variable' must be the identifier of an existing &lt;compartment&gt;, &lt;species&gt;, globally-defined &lt;parameter&gt;, or (in Level 3) &lt;speciesReference&gt;, or (in Level 3 Version 2), any identifier in the SId namespace of the model belonging to an element defined by an SBML Level 3 package as having with mathematical meaning.
- `20903` (error): Any &lt;compartment&gt;, &lt;species&gt;, &lt;parameter&gt;, or (in Level 3) &lt;speciesReference&gt; whose identifier is the value of a 'variable' attribute in an &lt;assignmentRule&gt;, must have a value of 'false' for 'constant'.
- `20911` (error): The value of a &lt;rateRule&gt; or &lt;assignmentRule&gt;'s 'variable' attribute must not be the identifier of a &lt;compartment&gt; with a 'spatialDimensions' value of 0.

<span id="math"></span>**math**

The math is an arbitrary expression which returns a number. Its units should be the units of the variable.

The report renders the formula in the column "math" and in the inspector.

Default: how the rule behaves mathematically stays undefined.

- `20907` (error): Every AssignmentRule, RateRule and AlgebraicRule object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the formula as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the formula from the units of the quantities it uses. They should be the units of the variable the rule assigns to.

## Validation rules

- `10705` (warning): The value of the 'sboTerm' attribute on a rule is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a mathematical expression (i.e., terms derived from SBO:0000064, "mathematical expression"). Note: This applies to Algebraic Rules in addition to Rate and Assignment Rules.
- `20906` (error): There must not be circular dependencies in the combined set of &lt;initialAssignment&gt;, &lt;assignmentRule&gt; and &lt;kineticLaw&gt; definitions in a model. Each of these constructs has the effect of assigning a value to an identifier (i.e. the identifier given in the field 'symbol' in &lt;initialAssignment&gt;, the field 'variable' in &lt;assignmentRule&gt;, and the field 'id' on the &lt;kineticLaw&gt;'s enclosing &lt;reaction&gt;). Each of these constructs computes the value using a mathematical formula. The formula for a given identifier cannot make reference to a second identifier whose own definition depends directly or indirectly on the first identifier.
- `20908` (error): An AssignmentRule object must have the required attribute 'variable' and may have the optional attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on an AssignmentRule object.

## Related elements

- [RateRule](raterule.md): a formula which gives the rate of change of an element
- [AlgebraicRule](algebraicrule.md): an equation which has to hold at every moment of the simulation
- [InitialAssignment](initialassignment.md): a formula which computes the value of an element at the start of the simulation

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.9.3 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
