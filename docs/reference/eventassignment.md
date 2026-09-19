# EventAssignment

The new value an event gives to one element of the model.

An event assignment sets a compartment, a species, a stoichiometry or a parameter to the value of its formula at the moment the event is executed. The element must not be constant, because a constant cannot be changed by an event.

The report shows an event assignment as an element of its own, with a link to the element it changes and the rendered formula.

## Attributes

| attribute | type | required | meaning | specification |
| --- | --- | --- | --- | --- |
| [variable](#variable) | [`SIdRef`](datatypes.md#sidref) | required | the element the assignment changes | [core 4.12.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |
| [math](#math) | [`Math`](datatypes.md#math) | optional | the formula which computes the new value | [core 4.12.5](https://sbml.org/documents/specifications/level-3/version-2/core/) |

Every element of a model also carries the [common attributes](sbase.md) of `SBase`.

<span id="variable"></span>**variable**

The variable names the compartment, species, species reference or parameter which receives the new value. It must not be constant.

The report links the named element in the table of the event and in the inspector.

- `10305` (error): In each &lt;event&gt;, the value of the 'variable' field within every &lt;eventAssignment&gt; definition must be unique across the set of all &lt;eventAssignment&gt;s within that &lt;event&gt;.
- `10306` (error): An identifier used as the value of 'variable' in an &lt;eventAssignment&gt; cannot also appear as the value of 'variable' in an &lt;assignmentRule&gt;.
- `21211` (error): The value of the attribute 'variable' in an &lt;eventAssignment&gt; can only be the identifier of a &lt;compartment&gt;, &lt;species&gt;, model-wide &lt;parameter&gt; definition, or (in Level 3) &lt;speciesReference&gt;, or (in Level 3 Version 2), any identifier in the SId namespace of the model belonging to an element defined by an SBML Level 3 package as having with mathematical meaning.
- `21212` (error): Any &lt;compartment&gt;, &lt;species&gt;, &lt;parameter&gt;, or (in Level 3) &lt;speciesReference&gt; definition whose identifier is used as the value of 'variable' in an &lt;eventAssignment&gt; must have a value of 'false' for its 'constant' attribute.

<span id="math"></span>**math**

The math is an arbitrary expression over the elements of the model. Whether it is evaluated when the event triggers or when it is executed is decided by the flag "values from trigger time" of the event.

The report renders the formula in the table of the event and in the inspector.

Default: nothing is assigned when the event is executed.

- `21213` (error): An EventAssignment object must contain exactly one MathML &lt;math&gt; element. The &lt;math&gt; element is optional in L3V2 and beyond.

## Validation rules

- `10711` (warning): The value of the 'sboTerm' attribute on an &lt;eventAssignment&gt; is expected to be an SBO identifier (http://www.biomodels.net/SBO/) referring to a mathematical expression (i.e., terms derived from SBO:0000064, "mathematical expression").
- `21214` (error): An EventAssignment object must have the required attribute 'variable' and may have the optional attributes 'metaid' and 'sboTerm'. No other attributes from the SBML Level 3 Core namespace are permitted on an EventAssignment object.

## Related elements

- [Event](event.md): an instantaneous change of the model when a condition becomes true
- [AssignmentRule](assignmentrule.md): a formula which holds at every moment of the simulation

## Specification

[SBML Level 3 Version 2 Core](https://sbml.org/documents/specifications/level-3/version-2/core/), Section 4.12.5 (Hucka et al. 2019, J Integr Bioinform 16(2):20190021).
