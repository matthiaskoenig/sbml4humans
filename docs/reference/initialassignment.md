# InitialAssignment

A formula which computes the value of an element at the start of the simulation.

An initial assignment computes the value of a compartment, a species, a parameter or a stoichiometry before the simulation starts, from the values of other elements. It exists because the attributes of an element can only hold a literal number, and an initial value is often derived from other quantities. It applies up to the start of time and, unlike an assignment rule, it may also set a constant.

The report shows the element which is assigned, the rendered formula and the units the formula produces.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [symbol](#symbol) | [`SIdRef`](datatypes.md#sidref) | required | the element whose initial value the assignment computes | [core 4.8.2](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula which computes the initial value | [core 4.8.3](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="symbol"></span>**symbol**

The symbol names the compartment, species, species reference or parameter which receives the value. It is called symbol rather than variable because an initial assignment may also set an element which is constant.

The report links the named element in the column "symbol" and in the inspector.

- `20801` (error): The value of 'symbol' in an &lt;initialAssignment&gt; definition must be the identifier of an existing &lt;compartment&gt;, &lt;species&gt;, or &lt;parameter&gt; defined in the model or &lt;speciesReference&gt; in Level 3, or in Level 3 Version 2, any identifier in the SId namespace of the model belonging to an element defined by an SBML Level 3 package as having with mathematical meaning.
- `20802` (error): A given identifier cannot appear as the value of more than one 'symbol' field across the set of &lt;initialAssignment&gt;s in a model.
- `20803` (error): The value of a 'symbol' field in any &lt;initialAssignment&gt; definition cannot also appear as the value of a 'variable' field in an &lt;assignmentRule&gt;.
- `20806` (error): The identifier given as the value of a 'symbol' attribute in any &lt;initialAssignment&gt; definition cannot be the identifier of a &lt;compartment&gt; with a 'spatialDimensions' value of 0.

<span id="math"></span>**math**

The math is an arbitrary expression over the elements of the model. Its units should be the units of the element it assigns to.

The report renders the formula in the column "math" and in the inspector.

Default: what is assigned to the symbol stays undefined.

- `20804` (error): An InitialAssignment object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

## In the report

| field | type | meaning |
| --- | --- | --- |
| [derived units](#derived-units) | [`latex`](datatypes.md#latex) | the units of the formula as the report derives them |

<span id="derived-units"></span>**derived units**

The report derives the units of the formula from the units of the quantities it uses and renders them as a formula. Comparing them with the units of the assigned element is the quickest check of an initial assignment.

## Validation rules

- `10704` (warning): The value of the 'sboTerm' attribute on an &lt;initialAssignment&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a mathematical expression (i.e., terms derived from SBO:0000064, "mathematical expression").
- `20805` (error): An InitialAssignment object must have the required attribute 'symbol' and may have the optional attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on an InitialAssignment object.
- `20906` (error): There must not be circular dependencies in the combined set of &lt;initialAssignment&gt;, &lt;assignmentRule&gt; and &lt;kineticLaw&gt; definitions in a model. Each of these constructs has the effect of assigning a value to an identifier (i.e. the identifier given in the field 'symbol' in &lt;initialAssignment&gt;, the field 'variable' in &lt;assignmentRule&gt;, and the field 'id' on the &lt;kineticLaw&gt;'s enclosing &lt;reaction&gt;). Each of these constructs computes the value using a mathematical formula. The formula for a given identifier cannot make reference to a second identifier whose own definition depends directly or indirectly on the first identifier.

## Related elements

- [AssignmentRule](assignmentrule.md): a formula which holds at every moment of the simulation
- [Parameter](parameter.md): a named value which the mathematics of the model can use
- [Species](species.md): a pool of a chemical entity in a compartment
- [Compartment](compartment.md): a bounded space in which species are located

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.8 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
